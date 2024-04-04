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

        # Add widgets with the test details, centering the text
        # Note: Set `halign` and `valign` to 'center'. Also, ensure `text_size` is set for valign to work effectively.
        antigen_label = Label(text=f'Antigen: {antigen}', size_hint_y=None, height=40, halign='center', valign='center')
        antigen_label.text_size = antigen_label.size  # This ensures the text is centered vertically within its allocated space
        content.add_widget(antigen_label)

        result_label = Label(text=f'Result: {result} Concentration', size_hint_y=None, height=40, halign='center', valign='center')
        result_label.text_size = result_label.size
        content.add_widget(result_label)

        date_label = Label(text=f'Date: {date}', size_hint_y=None, height=40, halign='center', valign='center')
        date_label.text_size = date_label.size
        content.add_widget(date_label)

        # Close button
        close_button = Button(text='Close', size_hint_y=None, height=40)
        close_button.bind(on_press=lambda *args: self.dismiss()) # type: ignore
        content.add_widget(close_button)

        self.add_widget(content)

        # Bind size changes to update text_size dynamically
        antigen_label.bind(size=lambda *x: setattr(antigen_label, 'text_size', antigen_label.size)) # type: ignore
        result_label.bind(size=lambda *x: setattr(result_label, 'text_size', result_label.size)) # type: ignore
        date_label.bind(size=lambda *x: setattr(date_label, 'text_size', date_label.size)) # type: ignore
