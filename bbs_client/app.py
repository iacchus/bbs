from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal, VerticalScroll
from textual.widgets import Header, Footer, Input, Button, Label, Select, DataTable, Static, TextArea, Tree
from textual.screen import Screen, ModalScreen
from textual import on, work
from textual.reactive import reactive
import asyncio

from .database import init_db, get_all_identities, add_identity, IdentityRecord
from .auth import generate_identity, Identity
from .api import BBSClient

class ConnectionManager(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Label("Server URL:"),
            Input(placeholder="http://localhost:8100", value="http://localhost:8100", id="server_url"),
            Label("Identity:"),
            Select([], id="identity_select", prompt="Select Identity"),
            Button("New Identity", id="new_identity_btn"),
            Button("Connect", id="connect_btn", variant="primary"),
            id="connection_form"
        )
        yield Footer()

    async def on_mount(self) -> None:
        self.identities = await get_all_identities()
        options = [(i.name, i.private_key) for i in self.identities]
        select = self.query_one("#identity_select")
        select.set_options(options)
        if options:
            select.value = options[0][1] # Select first by default

    @on(Button.Pressed, "#new_identity_btn")
    def new_identity(self):
        self.app.push_screen(NewIdentityModal())

    @on(Button.Pressed, "#connect_btn")
    async def connect(self):
        url = self.query_one("#server_url").value
        private_key = self.query_one("#identity_select").value

        if not url or not private_key:
            self.notify("Please select a server and identity.", severity="error")
            return

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

        screen = self.app.get_screen("connection")
        if isinstance(screen, ConnectionManager):
             screen.identities = await get_all_identities()
             options = [(i.name, i.private_key) for i in screen.identities]
             select = screen.query_one("#identity_select")
             select.set_options(options)
             select.value = identity.private_key

        self.dismiss()

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
            Button("New Board", id="new_board_btn")
        )
        yield Footer()

    async def on_mount(self) -> None:
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
            Button("New Thread", id="new_thread_btn")
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
        self.app.push_screen(ComposeModal(board_id=self.board_id))

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
            Button("Reply to Thread", id="reply_btn")
        )
        yield Footer()

    async def on_mount(self) -> None:
        await self.load_thread()

    @on(Button.Pressed, "#back_btn")
    def back(self):
        self.app.pop_screen()

    @on(Button.Pressed, "#reply_btn")
    def reply(self):
        # Reply to OP (thread_id)
        self.app.push_screen(ComposeModal(thread_id=self.thread_id))

    @on(Button.Pressed, "#refresh_btn")
    async def load_thread(self):
        container = self.query_one("#posts_container")
        container.remove_children()

        try:
            data = await self.app.client.get_thread(self.thread_id)
            thread = data.get("thread", {})
            posts = data.get("posts", [])

            # Display OP
            container.mount(Label(f"Title: {thread.get('title')}", classes="thread_title"))
            content = thread.get("content", "")
            author = thread.get("author_pubkey", "")[:8]
            op_id = thread.get("id")

            op_widget = Vertical(
                    Label(f"#{op_id} by {author} (OP)", classes="post_header"),
                    Static(content, classes="post_content"),
                    classes="post_item"
            )
            container.mount(op_widget)

            # Display Replies
            for post in posts:
                content = post.get("content", "")
                author = post.get("author_pubkey", "")[:8]
                pid = post.get("id")

                post_widget = Vertical(
                    Label(f"#{pid} by {author}", classes="post_header"),
                    Static(content, classes="post_content"),
                    Button("Reply", id=f"reply_{pid}", classes="reply_small_btn"),
                    classes="post_item"
                )
                container.mount(post_widget)

        except Exception as e:
            self.notify(f"Error loading thread: {e}", severity="error")

    @on(Button.Pressed)
    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id and event.button.id.startswith("reply_"):
            try:
                post_id = int(event.button.id.split("_")[1])
                # Reply to a specific post
                self.app.push_screen(ComposeModal(thread_id=self.thread_id, parent_id=post_id))
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

class BBSApp(App):
    CSS = """
    ConnectionManager, NewIdentityModal, ComposeModal, NewBoardModal {
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
        border: solid gray;
        margin: 1;
        padding: 1;
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
