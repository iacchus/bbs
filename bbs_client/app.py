from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal, VerticalScroll
from textual.widgets import Header, Footer, Input, Button, Label, Select, DataTable, Static, TextArea, Tree
from textual.screen import Screen, ModalScreen
from textual import on, work
from textual.reactive import reactive
import asyncio

from .database import init_db, get_all_identities, add_identity, IdentityRecord, delete_identity, update_identity_name
from .auth import generate_identity, Identity
from .api import BBSClient
from .servers import load_servers, save_servers
import uuid

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
                Button("New", id="new_identity_btn"),
                Button("Rename", id="rename_identity_btn", disabled=True),
                Button("Delete", id="delete_identity_btn", variant="error", disabled=True),
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
            url = f"http://{s['address']}:{s['port']}"
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
        self.identities = await get_all_identities()
        options = [(i.name, i.private_key) for i in self.identities]
        select = self.query_one("#identity_select")
        select.set_options(options)
        
        if select_pk:
            select.value = select_pk
        elif options:
            select.value = options[0][1]
        else:
            select.clear()
        
        # 1. Disable buttons if no credential is selected
        has_selection = not select.is_blank()
        self.query_one("#rename_identity_btn").disabled = not has_selection
        self.query_one("#delete_identity_btn").disabled = not has_selection

    @on(Select.Changed, "#identity_select")
    def on_identity_change(self, event: Select.Changed):
        has_selection = not self.query_one("#identity_select").is_blank()
        self.query_one("#rename_identity_btn").disabled = not has_selection
        self.query_one("#delete_identity_btn").disabled = not has_selection

    @on(Button.Pressed, "#new_identity_btn")
    def new_identity(self):
        def after_create(result):
            if result:
                self.run_worker(self.refresh_identities(select_pk=result))
        self.app.push_screen(NewIdentityModal(), after_create)

    @on(Button.Pressed, "#rename_identity_btn")
    async def rename_identity(self):
        pk = self.query_one("#identity_select").value
        if not pk:
            self.notify("No identity selected", severity="error")
            return
        
        identity = next(i for i in self.identities if i.private_key == pk)
        
        def do_rename(new_name):
            if new_name:
                async def run_rename():
                    await update_identity_name(pk, new_name)
                    await self.refresh_identities(select_pk=pk)
                    self.notify(f"Identity renamed to {new_name}")
                self.run_worker(run_rename())

        self.app.push_screen(EditNameModal(identity.name), do_rename)

    @on(Button.Pressed, "#delete_identity_btn")
    async def confirm_delete(self):
        pk = self.query_one("#identity_select").value
        if not pk:
            self.notify("No identity selected", severity="error")
            return

        def do_delete(confirmed):
            if confirmed:
                async def run_delete():
                    await delete_identity(pk)
                    await self.refresh_identities()
                    self.notify("Identity deleted")
                self.run_worker(run_delete())

        self.app.push_screen(ConfirmModal("Are you sure you want to delete this identity?"), do_delete)

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
            
        url = f"http://{server['address']}:{server['port']}"

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
        yield DataTable(id="server_table")
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

    @on(DataTable.RowSelected, "#server_table")
    def on_row_selected(self, event: DataTable.RowSelected):
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
    async def create(self):
        name = self.query_one("#nickname").value
        if not name:
            self.notify("Name required.", severity="error")
            return

        identity = generate_identity(name)
        await add_identity(identity.name, identity.private_key, identity.public_key)
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

class BoardList(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Label("Boards", id="screen_title")
        yield DataTable(id="board_table")
        yield Horizontal(
            Button("Refresh", id="refresh_btn"),
            Button("New Board", id="new_board_btn", classes="hidden" if self.app.client.role != "admin" else ""),
            classes="button-bar"
        )
        yield Footer()

    async def on_mount(self) -> None:
        # Update header with role
        header = self.query_one(Header)
        header.tall = True
        if self.app.client.identity:
            self.title = f"BBS - {self.app.client.identity.name}"
            self.sub_title = f"Role: {self.app.client.role}"
        
        table = self.query_one("#board_table")
        table.add_columns("ID", "Name", "Description")
        table.cursor_type = "row"
        await self.load_boards()

    @on(Button.Pressed, "#refresh_btn")
    async def load_boards(self):
        table = self.query_one("#board_table")
        table.clear()
        try:
            boards = await self.app.client.get_boards()
            for board in boards:
                table.add_row(board["id"], board["name"], board["description"])
        except Exception as e:
            self.notify(f"Error loading boards: {e}", severity="error")

    @on(Button.Pressed, "#new_board_btn")
    def new_board(self):
        def after_submit(result):
             if result:
                 self.run_worker(self.load_boards())

        self.app.push_screen(NewBoardModal(), after_submit)

    @on(DataTable.RowSelected)
    def on_row_selected(self, event: DataTable.RowSelected):
        row_key = event.row_key
        row = self.query_one("#board_table").get_row(row_key)
        board_id = row[0]
        self.app.push_screen(ThreadList(board_id=board_id))


class ThreadList(Screen):
    def __init__(self, board_id: int):
        super().__init__()
        self.board_id = board_id

    def compose(self) -> ComposeResult:
        yield Header()
        yield Label(f"Board {self.board_id}", id="screen_title")
        yield DataTable(id="thread_table")
        yield Horizontal(
            Button("Back", id="back_btn"),
            Button("Refresh", id="refresh_btn"),
            Button("New Thread", id="new_thread_btn"),
            classes="button-bar"
        )
        yield Footer()

    async def on_mount(self) -> None:
        table = self.query_one("#thread_table")
        table.add_columns("ID", "Title", "Author")
        table.cursor_type = "row"
        await self.load_threads()

    @on(Button.Pressed, "#back_btn")
    def back(self):
        self.app.pop_screen()

    @on(Button.Pressed, "#refresh_btn")
    async def load_threads(self):
        table = self.query_one("#thread_table")
        table.clear()
        try:
            threads = await self.app.client.get_threads(self.board_id)
            for thread in threads:
                # Assuming thread is a Post object (OP)
                # It has title, author_pubkey
                table.add_row(thread["id"], thread["title"], thread["author_pubkey"][:10]+"...")
        except Exception as e:
            self.notify(f"Error loading threads: {e}", severity="error")

    @on(Button.Pressed, "#new_thread_btn")
    def new_thread(self):
        def after_submit(result):
            if result:
                self.run_worker(self.load_threads())
        self.app.push_screen(ComposeModal(board_id=self.board_id), after_submit)

    @on(DataTable.RowSelected)
    def on_row_selected(self, event: DataTable.RowSelected):
        row = self.query_one("#thread_table").get_row(event.row_key)
        thread_id = row[0]
        self.app.push_screen(ThreadView(thread_id=thread_id))

class ThreadView(Screen):
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

            # 2. Recursive render function
            def render_post(post, depth=0):
                content = post.get("content", "")
                author = post.get("author_pubkey", "")[:8]
                pid = post.get("id")
                is_op = (pid == self.thread_id)

                # The actual post content
                post_widget = Vertical(
                    Label(f"#{pid} by {author}{' (OP)' if is_op else ''}", classes="post_header"),
                    Static(content, classes="post_content"),
                    Button("Reply", id=f"reply_{pid}", classes="reply_small_btn"),
                    classes="post_item"
                )

                if depth == 0:
                    # Separate OP from its replies with a thin bottom border
                    post_widget.add_class("bottom_separator")
                    post_widget.styles.margin = (0, 0, 1, 0)
                    post_widget.styles.padding = (0, 0, 1, 0)

                # Recursively get children widgets
                child_widgets = [render_post(child, depth + 1) for child in children_map.get(pid, [])]

                # Create the branch container with post and children as initial widgets
                branch = Vertical(post_widget, *child_widgets, classes="thread_branch")
                
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

    @on(Button.Pressed)
    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id and event.button.id.startswith("reply_"):
            try:
                post_id = int(event.button.id.split("_")[1])
                def after_submit(result):
                    if result:
                        self.run_worker(self.load_thread())
                # Reply to a specific post
                self.app.push_screen(ComposeModal(thread_id=self.thread_id, parent_id=post_id), after_submit)
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
    #board_table, #thread_table, #posts_container {
        height: 1fr;
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
        init_db()
        self.push_screen("connection")

def run():
    app = BBSApp()
    app.run()

if __name__ == "__main__":
    run()
