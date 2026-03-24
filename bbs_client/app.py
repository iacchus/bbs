from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal, VerticalScroll
from textual.widgets import Header, Footer, Input, Button, Label, Select, DataTable, Static, TextArea, Tree, ListView, ListItem
from textual.screen import Screen, ModalScreen
from textual import on, work, events
from textual.binding import Binding
from textual.reactive import reactive
import asyncio

from .identities import get_all_identities_sync, add_identity_sync, IdentityRecord, delete_identity_sync, update_identity_name_sync
from .auth import generate_identity, Identity
from .api import BBSClient
from .servers import load_servers, save_servers
import uuid

class VimDataTable(DataTable):
    BINDINGS = [
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
    ]

class VimListView(ListView):
    BINDINGS = [
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
    ]

class ConnectionManager(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Label("Server:"),
            Select([], id="server_select", prompt="Select Server"),
            Horizontal(
                Button("Manage Servers", id="manage_servers_btn"),
                classes="button-bar"
            ),
            Label("Identity:"),
            Select([], id="identity_select", prompt="Select Identity"),
            Horizontal(
                Button("Manage Identities", id="manage_identities_btn"),
                classes="button-bar"
            ),
            Button("Connect", id="connect_btn", variant="primary"),
            id="connection_form"
        )
        yield Footer()

    async def on_mount(self) -> None:
        self.refresh_servers()
        await self.refresh_identities()

    def refresh_servers(self, select_id: str = None):
        self.servers = load_servers()
        options = []
        for s in self.servers:
            url = f"{s['address']}:{s['port']}"
            display = f"{s['name']} ({url})"
            options.append((display, s['id']))
            
        select = self.query_one("#server_select")
        select.set_options(options)
        
        if select_id:
            select.value = select_id
        elif options:
            select.value = options[0][1]
        else:
            select.clear()

    async def refresh_identities(self, select_pk: str = None):
        self.identities = get_all_identities_sync()
        options = [(i.name, i.private_key) for i in self.identities]
        select = self.query_one("#identity_select")
        select.set_options(options)
        
        if select_pk:
            select.value = select_pk
        elif options:
            select.value = options[0][1]
        else:
            select.clear()

    @on(Button.Pressed, "#manage_identities_btn")
    def manage_identities(self):
        async def after_manage(result):
            await self.refresh_identities()
        self.app.push_screen(IdentityManager(), after_manage)

    @on(Button.Pressed, "#manage_servers_btn")
    def manage_servers(self):
        def after_manage(result):
            self.refresh_servers()
        self.app.push_screen(ServerManager(), after_manage)

    @on(Button.Pressed, "#connect_btn")
    async def connect(self):
        server_id = self.query_one("#server_select").value
        private_key = self.query_one("#identity_select").value

        if not server_id or not private_key or server_id == Select.BLANK or private_key == Select.BLANK:
            self.notify("Please select a server and identity.", severity="error")
            return
            
        server = next((s for s in self.servers if s['id'] == server_id), None)
        if not server:
            self.notify("Server not found.", severity="error")
            return
            
        url = f"{server['address']}:{server['port']}"

        record = next((i for i in self.identities if i.private_key == private_key), None)
        if not record:
             self.notify("Identity not found.", severity="error")
             return

        identity = Identity(record.name, record.private_key)

        self.app.client = BBSClient(base_url=url)

        try:
            success = await self.app.client.login(identity)
            if success:
                self.notify("Connected successfully!")
                self.app.push_screen(BoardList())
            else:
                self.notify("Login failed.", severity="error")
        except Exception as e:
            self.notify(f"Connection error: {e}", severity="error")


class ServerModal(ModalScreen):
    def __init__(self, server: dict = None):
        super().__init__()
        self.server = server or {}

    def compose(self) -> ComposeResult:
        title = "Edit Server" if self.server else "New Server"
        yield Vertical(
            Label(title),
            Label("Name:"),
            Input(value=self.server.get("name", ""), id="server_name"),
            Label("Address:"),
            Input(value=self.server.get("address", ""), id="server_address"),
            Label("Port:"),
            Input(value=str(self.server.get("port", "8100")), id="server_port"),
            Horizontal(
                Button("Cancel", id="cancel"),
                Button("Save", id="save", variant="primary")
            ),
            id="modal_container"
        )

    @on(Button.Pressed, "#cancel")
    def cancel(self):
        self.dismiss(None)

    @on(Button.Pressed, "#save")
    def save(self):
        name = self.query_one("#server_name").value
        address = self.query_one("#server_address").value
        port_str = self.query_one("#server_port").value

        if not name or not address or not port_str:
            self.notify("All fields required.", severity="error")
            return

        try:
            port = int(port_str)
        except ValueError:
            self.notify("Port must be a number.", severity="error")
            return

        self.dismiss({
            "id": self.server.get("id", str(uuid.uuid4())),
            "name": name,
            "address": address,
            "port": port
        })

class ServerManager(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Label("Server Manager", id="screen_title")
        yield VimDataTable(id="server_table")
        yield Horizontal(
            Button("Back", id="back_btn"),
            Button("New Server", id="new_server_btn"),
            Button("Edit Selected", id="edit_server_btn", disabled=True),
            Button("Delete Selected", id="delete_server_btn", variant="error", disabled=True),
            classes="button-bar"
        )
        yield Footer()

    def on_mount(self):
        table = self.query_one("#server_table")
        table.add_columns("Name", "Address", "Port")
        table.cursor_type = "row"
        self.load_table()

    def load_table(self):
        self.servers = load_servers()
        table = self.query_one("#server_table")
        table.clear()
        for s in self.servers:
            table.add_row(s["name"], s["address"], str(s["port"]), key=s["id"])
            
        has_rows = len(table.rows) > 0
        if not has_rows:
            self.query_one("#edit_server_btn").disabled = True
            self.query_one("#delete_server_btn").disabled = True

    @on(VimDataTable.RowSelected, "#server_table")
    def on_row_selected(self, event: VimDataTable.RowSelected):
        self.query_one("#edit_server_btn").disabled = False
        self.query_one("#delete_server_btn").disabled = False

    @on(Button.Pressed, "#back_btn")
    def back(self):
        self.dismiss(True)

    @on(Button.Pressed, "#new_server_btn")
    def new_server(self):
        def after_new(server_data):
            if server_data:
                self.servers.append(server_data)
                save_servers(self.servers)
                self.load_table()
        self.app.push_screen(ServerModal(), after_new)

    @on(Button.Pressed, "#edit_server_btn")
    def edit_server(self):
        table = self.query_one("#server_table")
        if table.cursor_row is None:
            return
        row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key
        server_id = row_key.value
        server = next((s for s in self.servers if s["id"] == server_id), None)
        if server:
            def after_edit(server_data):
                if server_data:
                    for i, s in enumerate(self.servers):
                        if s["id"] == server_id:
                            self.servers[i] = server_data
                            break
                    save_servers(self.servers)
                    self.load_table()
            self.app.push_screen(ServerModal(server), after_edit)

    @on(Button.Pressed, "#delete_server_btn")
    def delete_server(self):
        table = self.query_one("#server_table")
        if table.cursor_row is None:
            return
        row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key
        server_id = row_key.value
        
        def do_delete(confirmed):
            if confirmed:
                self.servers = [s for s in self.servers if s["id"] != server_id]
                save_servers(self.servers)
                self.load_table()
                
        self.app.push_screen(ConfirmModal("Are you sure you want to delete this server?"), do_delete)

class IdentityManager(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Label("Identity Manager", id="screen_title")
        yield VimDataTable(id="identity_table")
        yield Horizontal(
            Button("Back", id="back_btn"),
            Button("New Identity", id="new_identity_btn"),
            Button("Rename", id="rename_identity_btn", disabled=True),
            Button("Delete", id="delete_identity_btn", variant="error", disabled=True),
            classes="button-bar"
        )
        yield Footer()

    async def on_mount(self) -> None:
        table = self.query_one("#identity_table")
        table.add_columns("Name", "Public Key (partial)")
        table.cursor_type = "row"
        self.load_table()

    def load_table(self):
        self.identities = get_all_identities_sync()
        table = self.query_one("#identity_table")
        table.clear()
        for i in self.identities:
            table.add_row(i.name, i.private_key[:16] + "...", key=i.private_key)
            
        has_rows = len(table.rows) > 0
        if not has_rows:
            self.query_one("#rename_identity_btn").disabled = True
            self.query_one("#delete_identity_btn").disabled = True

    @on(VimDataTable.RowSelected, "#identity_table")
    def on_row_selected(self, event: VimDataTable.RowSelected):
        self.query_one("#rename_identity_btn").disabled = False
        self.query_one("#delete_identity_btn").disabled = False

    @on(Button.Pressed, "#back_btn")
    def back(self):
        self.dismiss(True)

    @on(Button.Pressed, "#new_identity_btn")
    def new_identity(self):
        def after_create(result):
            if result:
                self.load_table()
        self.app.push_screen(NewIdentityModal(), after_create)

    @on(Button.Pressed, "#rename_identity_btn")
    def rename_identity(self):
        table = self.query_one("#identity_table")
        if table.cursor_row is None:
            return
        row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key
        pk = row_key.value
        
        identity = next(i for i in self.identities if i.private_key == pk)
        
        def do_rename(new_name):
            if new_name:
                update_identity_name_sync(pk, new_name)
                self.load_table()
                self.notify(f"Identity renamed to {new_name}")

        self.app.push_screen(EditNameModal(identity.name), do_rename)

    @on(Button.Pressed, "#delete_identity_btn")
    def confirm_delete(self):
        table = self.query_one("#identity_table")
        if table.cursor_row is None:
            return
        row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key
        pk = row_key.value

        def do_delete(confirmed):
            if confirmed:
                delete_identity_sync(pk)
                self.load_table()
                self.notify("Identity deleted")

        self.app.push_screen(ConfirmModal("Are you sure you want to delete this identity?"), do_delete)

class NewIdentityModal(ModalScreen):
    def compose(self) -> ComposeResult:
        yield Vertical(
            Label("Enter Name:"),
            Input(placeholder="Nickname", id="nickname"),
            Horizontal(
                Button("Cancel", id="cancel"),
                Button("Create", id="create", variant="primary")
            ),
            id="modal_container"
        )

    @on(Button.Pressed, "#cancel")
    def cancel(self):
        self.dismiss()

    @on(Button.Pressed, "#create")
    def create(self):
        name = self.query_one("#nickname").value
        if not name:
            self.notify("Name required.", severity="error")
            return

        identity = generate_identity(name)
        add_identity_sync(name, identity.private_key, identity.public_key)
        self.notify(f"Identity '{name}' created!")

        self.dismiss(identity.private_key)

class EditNameModal(ModalScreen):
    def __init__(self, current_name: str):
        super().__init__()
        self.current_name = current_name

    def compose(self) -> ComposeResult:
        yield Vertical(
            Label("Edit Name:"),
            Input(value=self.current_name, id="new_name"),
            Horizontal(
                Button("Cancel", id="cancel"),
                Button("Save", id="save", variant="primary")
            ),
            id="modal_container"
        )

    @on(Button.Pressed, "#cancel")
    def cancel(self):
        self.dismiss(None)

    @on(Button.Pressed, "#save")
    def save(self):
        name = self.query_one("#new_name").value
        self.dismiss(name if name else None)

class ConfirmModal(ModalScreen):
    def __init__(self, message: str):
        super().__init__()
        self.message = message

    def compose(self) -> ComposeResult:
        yield Vertical(
            Label(self.message),
            Horizontal(
                Button("No", id="no"),
                Button("Yes", id="yes", variant="error")
            ),
            id="modal_container"
        )

    @on(Button.Pressed, "#no")
    def no(self):
        self.dismiss(False)

    @on(Button.Pressed, "#yes")
    def yes(self):
        self.dismiss(True)

class NewBoardModal(ModalScreen):
    def compose(self) -> ComposeResult:
        yield Vertical(
            Label("New Board"),
            Input(placeholder="Name", id="board_name"),
            Input(placeholder="Description", id="board_desc"),
            Horizontal(
                Button("Cancel", id="cancel"),
                Button("Create", id="create", variant="primary")
            ),
            id="modal_container"
        )

    @on(Button.Pressed, "#cancel")
    def cancel(self):
        self.dismiss()

    @on(Button.Pressed, "#create")
    async def create(self):
        name = self.query_one("#board_name").value
        desc = self.query_one("#board_desc").value

        if not name:
            self.notify("Name required.", severity="error")
            return

        try:
            await self.app.client.create_board(name, desc)
            self.notify(f"Board '{name}' created!")
            self.dismiss(result=True)
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")

class ProfileScreen(Screen):
    def __init__(self, public_key: str = None):
        super().__init__()
        self.public_key = public_key

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Label("User Profile", id="screen_title"),
            Label("Public Key:"),
            Input(value="", id="profile_pubkey", disabled=True),
            Label("Role:"),
            Input(value="", id="profile_role", disabled=True),
            Label("Username:"),
            Input(value="", id="profile_username", placeholder="Set a username (alphanumeric, hyphens, underscores)"),
            Horizontal(
                Button("Back", id="back_btn"),
                Button("Save", id="save_btn", variant="primary", classes="hidden"),
                classes="button-bar"
            ),
            id="profile_container"
        )
        yield Footer()

    async def on_mount(self) -> None:
        await self.load_profile()

    async def load_profile(self):
        try:
            profile = await self.app.client.get_profile(self.public_key)
            if profile:
                self.query_one("#profile_pubkey").value = profile.get("public_key", "")
                self.query_one("#profile_role").value = profile.get("role", "")
                self.query_one("#profile_username").value = profile.get("username", "") or ""
                
                # Only allow editing if it's our own profile
                # Assuming if self.public_key is None or matches our client identity, it's ours
                is_own = not self.public_key or self.public_key == self.app.client.identity.public_key
                
                if is_own:
                    self.query_one("#save_btn").remove_class("hidden")
                else:
                    self.query_one("#profile_username").disabled = True

        except Exception as e:
            self.notify(f"Error loading profile: {e}", severity="error")

    @on(Button.Pressed, "#back_btn")
    def back(self):
        self.app.pop_screen()

    @on(Button.Pressed, "#save_btn")
    async def save_profile(self):
        username = self.query_one("#profile_username").value.strip()
        try:
            await self.app.client.update_profile(username)
            self.notify("Profile updated successfully!")
            self.app.pop_screen()
        except Exception as e:
            self.notify(f"Error updating profile: {e}", severity="error")

class BoardListItem(ListItem):
    def __init__(self, board_id: int, name: str, description: str):
        super().__init__()
        self.board_id = board_id
        self.board_name = name
        self.description = description

    def compose(self) -> ComposeResult:
        yield Horizontal(
            Label(self.board_name, classes="list_col_name"),
            Label(self.description, classes="list_col_desc"),
            classes="list_item_layout"
        )

class ThreadListItem(ListItem):
    def __init__(self, thread_id: int, title: str, author: str):
        super().__init__()
        self.thread_id = thread_id
        self.title_str = title
        self.author = author

    def compose(self) -> ComposeResult:
        yield Horizontal(
            Label(self.title_str, classes="list_col_title"),
            Label(self.author, classes="list_col_author"),
            classes="list_item_layout"
        )

class BoardList(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Label("Boards", id="screen_title")
        yield VimListView(id="board_list")
        yield Horizontal(
            Button("Disconnect", id="disconnect_btn", variant="error"),
            Button("Profile", id="profile_btn"),
            Button("Refresh", id="refresh_btn"),
            Button("New Board", id="new_board_btn", classes="hidden" if self.app.client.role != "admin" else ""),
            classes="button-bar"
        )
        yield Footer()

    @on(Button.Pressed, "#profile_btn")
    def open_profile(self):
        self.app.push_screen(ProfileScreen(public_key=None))

    @on(Button.Pressed, "#disconnect_btn")
    def disconnect(self):
        self.app.pop_screen() # Should go back to connection manager if it was pushed

    async def on_mount(self) -> None:
        # Update header with role
        header = self.query_one(Header)
        header.tall = True
        if self.app.client.identity:
            self.title = f"BBS - {self.app.client.identity.name}"
            self.sub_title = f"Role: {self.app.client.role}"
        
        await self.load_boards()

    @on(Button.Pressed, "#refresh_btn")
    async def load_boards(self):
        list_view = self.query_one("#board_list")
        list_view.clear()
        try:
            boards = await self.app.client.get_boards()
            for board in boards:
                list_view.append(BoardListItem(board["id"], board["name"], board["description"]))
        except Exception as e:
            self.notify(f"Error loading boards: {e}", severity="error")

    @on(Button.Pressed, "#new_board_btn")
    def new_board(self):
        def after_submit(result):
             if result:
                 self.run_worker(self.load_boards())

        self.app.push_screen(NewBoardModal(), after_submit)

    @on(ListView.Selected, "#board_list")
    def on_list_selected(self, event: ListView.Selected):
        board_id = event.item.board_id
        self.app.push_screen(ThreadList(board_id=board_id))


class ThreadList(Screen):
    def __init__(self, board_id: int):
        super().__init__()
        self.board_id = board_id

    def compose(self) -> ComposeResult:
        yield Header()
        yield Label(f"Board {self.board_id}", id="screen_title")
        yield VimListView(id="thread_list")
        yield Horizontal(
            Button("Back", id="back_btn"),
            Button("Refresh", id="refresh_btn"),
            Button("New Thread", id="new_thread_btn"),
            classes="button-bar"
        )
        yield Footer()

    async def on_mount(self) -> None:
        await self.load_threads()

    @on(Button.Pressed, "#back_btn")
    def back(self):
        self.app.pop_screen()

    @on(Button.Pressed, "#refresh_btn")
    async def load_threads(self):
        list_view = self.query_one("#thread_list")
        list_view.clear()
        try:
            threads = await self.app.client.get_threads(self.board_id)
            for thread in threads:
                author_display = thread.get("author_username") or thread["author_pubkey"][:10]+"..."
                list_view.append(ThreadListItem(thread["id"], thread["title"], author_display))
        except Exception as e:
            self.notify(f"Error loading threads: {e}", severity="error")

    @on(Button.Pressed, "#new_thread_btn")
    def new_thread(self):
        def after_submit(result):
            if result:
                self.run_worker(self.load_threads())
        self.app.push_screen(ComposeModal(board_id=self.board_id), after_submit)

    @on(ListView.Selected, "#thread_list")
    def on_list_selected(self, event: ListView.Selected):
        thread_id = event.item.thread_id
        self.app.push_screen(ThreadView(thread_id=thread_id))

class PostItem(Vertical):
    can_focus = True
    
    BINDINGS = [
        Binding("enter", "reply", "Reply"),
        Binding("space", "toggle_collapse", "Toggle Collapse"),
        Binding("down", "focus_next", "Next", show=False),
        Binding("up", "focus_previous", "Previous", show=False),
        Binding("j", "focus_next", "Next (vim)", show=False),
        Binding("k", "focus_previous", "Previous (vim)", show=False),
    ]

    def __init__(self, pid: int, author: str, content: str, is_op: bool, children_count: int = 0, timestamp: str = "", **kwargs):
        super().__init__(**kwargs)
        self.pid = pid
        self.author = author
        self.post_content = content
        self.is_op = is_op
        self.children_count = children_count
        self.timestamp = timestamp
        self.is_collapsed = False

    def compose(self) -> ComposeResult:
        time_str = f" @ {self.timestamp}" if self.timestamp else ""
        yield Label(f"#{self.pid} by {self.author}{' (OP)' if self.is_op else ''}{time_str}", classes="post_header")
        yield Static(self.post_content, classes="post_content")
        
        expand_btn = Button(f" expand {self.children_count} replies ", id=f"expand_{self.pid}", classes="expand_btn hidden")
        expand_btn.can_focus = False
        reply_btn = Button("Reply", id=f"reply_{self.pid}", classes="reply_small_btn")
        reply_btn.can_focus = False
        
        yield Horizontal(
            expand_btn,
            Static(classes="reply_spacer"),
            reply_btn,
            classes="reply_container"
        )

    def on_focus(self, event: events.Focus):
        def do_scroll():
            try:
                container = self.app.query_one("#posts_container", VerticalScroll)
                container.scroll_to_center(self)
            except Exception:
                pass
        # Small delay to let the layout recalculate after display changes
        self.set_timer(0.05, do_scroll)

    @on(Button.Pressed)
    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id and event.button.id.startswith("expand_"):
            self.action_toggle_collapse()

    async def on_click(self, event: events.Click):
        if isinstance(event.widget, Label) and event.widget.has_class("post_header"):
            self.action_toggle_collapse()

    def action_toggle_collapse(self):
        branch = self.parent
        if branch and branch.has_class("thread_branch"):
            try:
                self.is_collapsed = not self.is_collapsed
                # toggle display of all children inside the branch except the first widget (which is this post)
                for child in branch.children:
                    if child != self:
                        child.display = not self.is_collapsed
                        
                expand_btn = self.query_one(f"#expand_{self.pid}", Button)
                if self.is_collapsed and self.children_count > 0:
                    expand_btn.remove_class("hidden")
                    self.add_class("collapsed")
                else:
                    expand_btn.add_class("hidden")
                    self.remove_class("collapsed")
            except Exception:
                pass
                
    def action_reply(self):
        try:
            self.app.query_one("ThreadView").post_reply(self.pid)
        except Exception:
            pass

    def action_focus_next(self):
        posts = list(self.screen.query("PostItem"))
        try:
            idx = posts.index(self)
            if idx + 1 < len(posts):
                posts[idx + 1].focus()
        except ValueError:
            pass

    def action_focus_previous(self):
        posts = list(self.screen.query("PostItem"))
        try:
            idx = posts.index(self)
            if idx - 1 >= 0:
                posts[idx - 1].focus()
        except ValueError:
            pass

class ThreadView(Screen):
    BINDINGS = [
        Binding("j", "focus_first_post", "Focus Posts", show=False),
        Binding("k", "focus_first_post", "Focus Posts", show=False),
    ]

    def action_focus_first_post(self):
        posts = list(self.query("PostItem"))
        if posts:
            posts[0].focus()

    def __init__(self, thread_id: int):
        super().__init__()
        self.thread_id = thread_id

    def compose(self) -> ComposeResult:
        yield Header()
        yield Label("Thread View", id="screen_title")
        yield VerticalScroll(id="posts_container")
        yield Horizontal(
            Button("Back", id="back_btn"),
            Button("Refresh", id="refresh_btn"),
            Button("Reply to Thread", id="reply_btn"),
            classes="button-bar"
        )
        yield Footer()

    async def on_mount(self) -> None:
        await self.load_thread()

    @on(Button.Pressed, "#back_btn")
    def back(self):
        self.app.pop_screen()

    @on(Button.Pressed, "#reply_btn")
    def reply(self):
        def after_submit(result):
            if result:
                self.run_worker(self.load_thread())
        self.app.push_screen(ComposeModal(thread_id=self.thread_id), after_submit)

    @on(Button.Pressed, "#refresh_btn")
    async def load_thread(self):
        container = self.query_one("#posts_container")
        container.remove_children()

        try:
            data = await self.app.client.get_thread(self.thread_id)
            op = data.get("thread", {})
            posts = data.get("posts", [])

            if not op:
                self.notify("Thread not found.", severity="error")
                return

            # 1. Build a parent -> children map
            children_map = {}
            for p in posts:
                parent_id = p.get("reply_to_id")
                if parent_id:
                    children_map.setdefault(parent_id, []).append(p)

            def get_total_children(pid: int) -> int:
                count = 0
                for child in children_map.get(pid, []):
                    count += 1 + get_total_children(child["id"])
                return count

            # 2. Recursive render function
            def render_post(post, depth=0):
                content = post.get("content", "")
                author = post.get("author_username") or post.get("author_pubkey", "")[:8]
                pid = post.get("id")
                is_op = (pid == self.thread_id)
                children_count = get_total_children(pid)
                
                created_at_str = post.get("created_at")
                timestamp_str = ""
                if created_at_str:
                    try:
                        import datetime
                        dt = datetime.datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                        timestamp_str = dt.astimezone(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
                    except Exception:
                        pass

                # The actual post content
                post_widget = PostItem(pid=pid, author=author, content=content, is_op=is_op, children_count=children_count, timestamp=timestamp_str, classes="post_item")

                if depth == 0:
                    # Separate OP from its replies with a thin bottom border
                    post_widget.add_class("bottom_separator")
                    post_widget.styles.margin = (0, 0, 1, 0)
                    post_widget.styles.padding = (0, 0, 1, 0)

                # Recursively get children widgets
                child_widgets = [render_post(child, depth + 1) for child in children_map.get(pid, [])]
                children_container = Vertical(*child_widgets, classes="children_container")
                children_container.styles.height = "auto"

                # Create the branch container with post and children as initial widgets
                branch = Vertical(post_widget, children_container, classes="thread_branch")
                
                # Styles
                if depth > 1:
                    color_idx = (depth - 2) % 6
                    branch.add_class(f"thread_border_{color_idx}")
                    # Nesting indents them naturally by adding a small margin
                    branch.styles.margin = (0, 0, 0, 1)
                    branch.styles.padding = (0, 0, 0, 1) # (top, right, bottom, left)
                elif depth == 1:
                    # Separate each first-level reply (and its children) from the next
                    branch.add_class("bottom_separator")
                    branch.styles.margin = (0, 0, 1, 0)
                    branch.styles.padding = (0, 0, 1, 0)

                branch.styles.height = "auto"
                
                return branch

            # Start rendering from OP
            container.mount(render_post(op, depth=0))

        except Exception as e:
            self.notify(f"Error loading thread: {e}", severity="error")

    def post_reply(self, post_id: int):
        def after_submit(result):
            if result:
                self.run_worker(self.load_thread())
        self.app.push_screen(ComposeModal(thread_id=self.thread_id, parent_id=post_id), after_submit)

    @on(Button.Pressed)
    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id and event.button.id.startswith("reply_"):
            try:
                post_id = int(event.button.id.split("_")[1])
                self.post_reply(post_id)
            except:
                pass

class ComposeModal(ModalScreen):
    def __init__(self, board_id: int = None, thread_id: int = None, parent_id: int = None):
        super().__init__()
        self.board_id = board_id
        self.thread_id = thread_id
        self.parent_id = parent_id

    def compose(self) -> ComposeResult:
        title = "New Thread" if self.board_id else "Reply"
        yield Vertical(
            Label(title),
            Input(placeholder="Title", id="post_title", classes="hidden" if not self.board_id else ""),
            TextArea(id="post_content"),
            Horizontal(
                Button("Cancel", id="cancel"),
                Button("Submit", id="submit", variant="primary")
            ),
            id="modal_container"
        )

    @on(Button.Pressed, "#cancel")
    def cancel(self):
        self.dismiss()

    @on(Button.Pressed, "#submit")
    async def submit(self):
        content = self.query_one("#post_content").text
        title = self.query_one("#post_title").value

        if not content:
            self.notify("Content required.", severity="error")
            return

        try:
            if self.board_id:
                if not title:
                     self.notify("Title required for new thread.", severity="error")
                     return
                await self.app.client.create_thread(self.board_id, title, content)
                self.notify("Thread created!")
            elif self.thread_id:
                # Reply to thread or post
                # If parent_id is set, reply to that post. If not, reply to thread (OP).
                # But api.create_post takes thread_id as the target ID.
                target_id = self.parent_id if self.parent_id else self.thread_id
                await self.app.client.create_post(self.thread_id, content, parent_id=target_id)
                self.notify("Reply posted!")

            self.dismiss(result=True)
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")

from textual.binding import Binding
import time

class BBSApp(App):
    BINDINGS = [
        Binding("ctrl+c", "quit_gracefully", "Quit", show=True, priority=True),
    ]

    def __init__(self):
        super().__init__()
        self.last_ctrl_c_time = 0

    def action_quit_gracefully(self):
        now = time.time()
        if now - self.last_ctrl_c_time < 2:
            self.exit()
        else:
            self.last_ctrl_c_time = now
            self.notify("Press Ctrl+C again to exit", timeout=2)

    CSS = """
    ConnectionManager, NewIdentityModal, ComposeModal, NewBoardModal, EditNameModal, ConfirmModal, ServerManager, ServerModal {
        align: center top;
    }

    .list_item_layout {
        layout: grid;
        grid-size: 2;
        grid-columns: 1fr 2fr;
        padding: 1;
        width: 100%;
        height: auto;
    }

    .list_col_name, .list_col_title {
        text-style: bold;
        color: $accent;
    }

    .list_col_desc, .list_col_author {
        color: $text-muted;
    }


    #connection_form {
        padding: 2;
        border: solid green;
        height: auto;
        width: 60%;
        margin-top: 2;
    }
    #modal_container {
        padding: 2;
        border: solid blue;
        background: $surface;
        width: 60%;
        height: auto;
        margin-top: 5;
    }
    .post_item {
        margin: 0;
        padding: 0 0 1 0;
        height: auto;
    }
    .post_item:focus {
        background: $boost;
    }
    .post_item.collapsed {
        border-bottom: heavy $primary;
    }
    .thread_branch {
        height: auto;
    }
    .post_header {
        background: $primary;
        color: $text;
        padding: 0 1;
    }
    .post_content {
        padding: 1;
    }
    .reply_small_btn {
        min-width: 10;
        height: 1;
        border: none;
    }
    .expand_btn {
        min-width: 15;
        height: 1;
        border: none;
        background: $primary;
        color: $text;
        text-style: bold;
    }
    .reply_spacer {
        width: 1fr;
    }
    .reply_container {
        height: auto;
    }
    .reply_small_btn {
        display: none;
    }
    .post_item:focus .reply_small_btn {
        display: block;
    }
    .hidden {
        display: none;
    }
    .thread_title {
        text-align: center;
        text-style: bold;
        padding: 1;
    }
    .bottom_separator {
        border-bottom: solid $primary 30%;
    }
    .thread_border_0 { border-left: solid $primary; }
    .thread_border_1 { border-left: solid $secondary; }
    .thread_border_2 { border-left: solid $success; }
    .thread_border_3 { border-left: solid $warning; }
    .thread_border_4 { border-left: solid $error; }
    .thread_border_5 { border-left: solid $accent; }
    #board_table, #thread_table, #server_table, #identity_table {
        height: 1fr;
    }
    VimDataTable {
        height: 1fr;
    }
    #posts_container {
        height: 1fr;
        padding: 1 2;
    }
    .button-bar {
        height: 3;
        margin: 1 0;
    }
    """

    SCREENS = {
        "connection": ConnectionManager,
        # "boards": BoardList # Removed from here, pushed manually
    }

    def on_mount(self):
        self.push_screen("connection")

def run():
    app = BBSApp()
    app.run()

if __name__ == "__main__":
    run()
