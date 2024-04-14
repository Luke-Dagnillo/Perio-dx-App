from kivy.uix.modalview import ModalView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty
from kivy.clock import Clock
from kivy.metrics import dp

class TestResultDetail(ModalView):
    label_width = NumericProperty(0)

    def __init__(self, antigen, result, date, **kwargs):
        super(TestResultDetail, self).__init__(**kwargs)
        self.size_hint = (0.8, 0.8)
        self.pos_hint = {'center_x': 0.5, 'center_y': 0.5}

        # Outer layout with padding and a spacer at the bottom
        outer_layout = BoxLayout(orientation='vertical', spacing=10, padding=10)

        # Content layout
        self.content_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=10)
        self.content_layout.bind(minimum_height=self.content_layout.setter('height')) # type: ignore

        # Add widgets with the test details
        antigen_label = Label(text=f'Antigen: {antigen}', size_hint_y=None, height=dp(40), halign='center')
        result_label = Label(text=f'Result: {result} Concentration', size_hint_y=None, height=dp(40), halign='center')
        date_label = Label(text=f'Date: {date}', size_hint_y=None, height=dp(40), halign='center')

        # Add the labels to the content layout
        self.content_layout.add_widget(antigen_label)
        self.content_layout.add_widget(result_label)
        self.content_layout.add_widget(date_label)

        # Center the content layout within the outer layout
        outer_layout.add_widget(Widget())  # Top spacer
        outer_layout.add_widget(self.content_layout)
        outer_layout.add_widget(Widget())  # Bottom spacer

        # Close button at the bottom
        close_button = Button(text='Close', size_hint_y=None, height=dp(50))
        close_button.bind(on_press=lambda *args: self.dismiss()) # type: ignore
        outer_layout.add_widget(close_button)

        # Finally, add the outer layout to the modal view
        self.add_widget(outer_layout)

        # Bind the update of label_width when the modal view size changes
        self.bind(size=self.update_label_width) # type: ignore

        # Initialize label_width with correct value
        Clock.schedule_once(lambda dt: self.update_label_width(), 0)

    def update_label_width(self, *args):
        # When the modal size changes, update the label_width property
        # Adjust text_size for all labels to fit the new width
        if self.content_layout.width > 0:
            self.label_width = self.content_layout.width
            for label in self.content_layout.children:
                label.text_size = (self.label_width, None)
                label.halign = 'center'
                label.valign = 'middle'
