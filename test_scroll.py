import asyncio
from textual.app import App, ComposeResult
from textual.widgets import Label, Button
from textual.containers import VerticalScroll, Vertical
from textual import events, on

class Post(Vertical):
    can_focus = True
    def compose(self) -> ComposeResult:
        yield Label("Header")
        yield Label("Content\n" * 5)
        yield Button("Reply", classes="reply_btn")

    def on_focus(self, event: events.Focus):
        # schedule centering after layout update
        def do_scroll():
            try:
                self.parent.scroll_to_center(self)
            except Exception as e:
                print("err", e)
        self.set_timer(0.01, do_scroll) # wait for layout to settle

class MyApp(App):
    CSS = """
    Post {
        border: solid green;
        margin: 1;
    }
    Post:focus {
        background: blue;
    }
    .reply_btn {
        display: none;
    }
    Post:focus .reply_btn {
        display: block;
    }
    """
    def compose(self) -> ComposeResult:
        with VerticalScroll() as vs:
            for i in range(10):
                yield Post()

async def test():
    app = MyApp()
    async with app.run_test() as pilot:
        await pilot.press("tab")
        await pilot.press("tab")
        await pilot.pause(0.1)

asyncio.run(test())
