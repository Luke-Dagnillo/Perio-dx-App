from kivy.uix.modalview import ModalView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout

class TestResultDetail(ModalView):
    def __init__(self, antigen, result, date, **kwargs):
        super(TestResultDetail, self).__init__(**kwargs)
        self.size_hint = (.5, .5)
        self.auto_dismiss = True

        # Create a layout for your content
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)

        # Add widgets with the test details
        content.add_widget(Label(text=f'Antigen: {antigen}', size_hint_y=None, height=30))
        content.add_widget(Label(text=f'Result: {result}', size_hint_y=None, height=30))
        content.add_widget(Label(text=f'Date: {date}', size_hint_y=None, height=30))

        # Close button
        close_button = Button(text='Close', size_hint_y=None, height=40)
        close_button.bind(on_press=lambda *args: self.dismiss()) # type: ignore
        content.add_widget(close_button)

        self.add_widget(content)