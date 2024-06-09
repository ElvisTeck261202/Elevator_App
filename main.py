from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.spinner import Spinner
from kivy.uix.gridlayout import GridLayout
from kivy.clock import Clock
from kivy.uix.togglebutton import ToggleButton

# Pantalla para seleccionar pisos en mantenimiento
class MaintenanceScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Layout vertical principal
        self.layout = BoxLayout(orientation='vertical')
        self.layout.add_widget(Label(text='Select Floors Under Maintenance', font_size=32))

        # Lista para almacenar los pisos en mantenimiento
        self.maintenance_floors = []

        # GridLayout para los botones de los pisos
        self.grid_layout = GridLayout(cols=3, size_hint_y=None)
        self.grid_layout.bind(minimum_height=self.grid_layout.setter('height'))

        # Crear botones para cada piso
        for i in range(1, 8):
            btn = ToggleButton(text=f'Floor {i}', size_hint_y=None, height=44)
            btn.bind(on_press=self.toggle_floor)
            self.grid_layout.add_widget(btn)

        self.layout.add_widget(self.grid_layout)

        # Botón para confirmar la selección de pisos en mantenimiento
        self.confirm_button = Button(text='Confirm', on_press=self.confirm_maintenance)
        self.layout.add_widget(self.confirm_button)

        self.add_widget(self.layout)

    # Método para alternar el estado de un piso (en mantenimiento o no)
    def toggle_floor(self, instance):
        floor = int(instance.text.split()[1])
        if instance.state == 'down':
            if floor not in self.maintenance_floors:
                self.maintenance_floors.append(floor)
        else:
            if floor in self.maintenance_floors:
                self.maintenance_floors.remove(floor)

    # Método para confirmar los pisos en mantenimiento y pasar a la pantalla de solicitudes
    def confirm_maintenance(self, instance):
        self.manager.get_screen('request').set_maintenance_floors(self.maintenance_floors)
        self.manager.current = 'request'

# Pantalla para agregar solicitudes de pisos
class RequestScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Layout vertical principal
        self.layout = BoxLayout(orientation='vertical')

        self.label = Label(text='Add Floor Request', font_size=32)
        self.layout.add_widget(self.label)

        # Spinner para seleccionar el piso de origen
        self.from_spinner = Spinner(
            text='Floor From',
            values=[str(i) for i in range(1, 8)],
            size_hint=(None, None),
            size=(200, 44)
        )
        self.layout.add_widget(self.from_spinner)

        # Spinner para seleccionar el piso de destino
        self.to_spinner = Spinner(
            text='Floor To',
            values=[str(i) for i in range(1, 8)],
            size_hint=(None, None),
            size=(200, 44)
        )
        self.layout.add_widget(self.to_spinner)

        # Botón para agregar la solicitud
        self.button = Button(text='Add Request', on_press=self.add_request)
        self.layout.add_widget(self.button)

        # Botón para ir a la pantalla del elevador
        self.go_to_elevator_button = Button(text='Go to Elevator', on_press=self.go_to_elevator)
        self.layout.add_widget(self.go_to_elevator_button)

        self.add_widget(self.layout)

    # Método para establecer los pisos en mantenimiento y actualizar los spinners
    def set_maintenance_floors(self, maintenance_floors):
        self.maintenance_floors = maintenance_floors
        available_floors = [str(i) for i in range(1, 8) if i not in self.maintenance_floors]
        self.from_spinner.values = available_floors
        self.to_spinner.values = available_floors

    # Método para agregar una solicitud de piso
    def add_request(self, instance):
        try:
            from_floor = int(self.from_spinner.text)
            to_floor = int(self.to_spinner.text)
            if from_floor == to_floor:
                raise ValueError("From and To floors cannot be the same")
            self.manager.get_screen('elevator').add_request(from_floor, to_floor)
            self.from_spinner.text = 'Floor From'
            self.to_spinner.text = 'Floor To'
        except ValueError:
            popup = Popup(title='Error',
                          content=Label(text='Please select valid and different floors'),
                          size_hint=(0.6, 0.4))
            popup.open()

    # Método para cambiar a la pantalla del elevador
    def go_to_elevator(self, instance):
        self.manager.current = 'elevator'

# Pantalla del elevador
class ElevatorScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_floor = 1
        self.requests = []
        self.moving = False

        # Layout horizontal principal
        self.layout = BoxLayout(orientation='horizontal')

        # Columna izquierda: Elevador
        elevator_column = GridLayout(cols=1, rows=7)
        self.elevator_labels = [Label(text='') for _ in range(7)]
        self.elevator_label = Label(text='Elevator', font_size=32)
        self.elevator_labels[6] = self.elevator_label  # Posición en el primer piso (última fila en la cuadrícula)

        for label in self.elevator_labels:
            elevator_column.add_widget(label)

        self.layout.add_widget(elevator_column)

        # Columna derecha: Pisos
        floors_column = BoxLayout(orientation='vertical')
        self.floor_labels = []
        for i in range(7, 0, -1):  # Asumiendo 7 pisos, de 7 hacia abajo a 1
            floor_label = Label(text=f'Floor {i}', font_size=24)
            self.floor_labels.append(floor_label)
            floors_column.add_widget(floor_label)

        self.layout.add_widget(floors_column)

        # Panel de información
        self.info_layout = BoxLayout(orientation='vertical')
        self.floor_label = Label(text=f"Current Floor: {self.current_floor}", font_size=32)
        self.info_layout.add_widget(self.floor_label)

        self.route_label = Label(text='Route: []', font_size=24)
        self.info_layout.add_widget(self.route_label)

        self.direction_label = Label(text='Direction: --', font_size=24)
        self.info_layout.add_widget(self.direction_label)

        self.status_label = Label(text='Status: Standing', font_size=24)
        self.info_layout.add_widget(self.status_label)

        self.go_to_request_button = Button(text='Add More Requests', on_press=self.go_to_request)
        self.info_layout.add_widget(self.go_to_request_button)

        self.layout.add_widget(self.info_layout)

        self.add_widget(self.layout)

    # Método para agregar una solicitud de piso
    def add_request(self, from_floor, to_floor):
        self.requests.append((from_floor, to_floor))
        self.update_route()

    # Método para actualizar la ruta del elevador
    def update_route(self):
        route = [f'{from_floor}->{to_floor}' for from_floor, to_floor in self.requests]
        self.route_label.text = f'Route: {route}'

    # Método para iniciar la animación del elevador al entrar en la pantalla
    def on_enter(self, *args):
        if self.requests and not self.moving:
            self.move_elevator()

    # Método para mover el elevador
    def move_elevator(self):
        if self.requests:
            self.moving = True
            self.status_label.text = 'Status: Moving'
            self.process_next_request()
        else:
            self.moving = False
            self.status_label.text = 'Status: Standing'

    # Método para procesar la siguiente solicitud
    def process_next_request(self):
        if not self.requests:
            self.moving = False
            self.status_label.text = 'Status: Standing'
            return

        from_floor, to_floor = self.requests.pop(0)
        self.update_route()

        self.move_to_floor(from_floor, lambda dt: Clock.schedule_once(
            lambda dt: self.move_to_floor(to_floor, self.on_floor_reached), 2))

    # Método para mover el elevador a un piso específico
    def move_to_floor(self, floor, on_complete):
        def move_step_by_step(current, target, direction, on_complete):
            if current == target:
                self.open_close_doors(on_complete)
                return

            next_floor = current + direction
            target_index = 7 - next_floor
            self.elevator_labels[target_index].text = 'Elevator'
            self.elevator_labels[7 - self.current_floor].text = ''
            self.current_floor = next_floor
            self.floor_label.text = f"Current Floor: {self.current_floor}"
            self.direction_label.text = 'Direction: Up' if direction > 0 else 'Direction: Down'

            Clock.schedule_once(lambda dt: move_step_by_step(next_floor, target, direction, on_complete), 0.5)

        direction = 1 if floor > self.current_floor else -1
        move_step_by_step(self.current_floor, floor, direction, on_complete)

    # Método para abrir y cerrar las puertas del elevador
    def open_close_doors(self, on_complete):
        self.status_label.text = 'Status: Doors Opening'
        Clock.schedule_once(lambda dt: self.close_doors(on_complete), 2)

    # Método para cerrar las puertas del elevador
    def close_doors(self, on_complete):
        self.status_label.text = 'Status: Doors Closing'
        Clock.schedule_once(on_complete, 2)

    # Método que se llama cuando se alcanza el piso deseado
    def on_floor_reached(self, dt):
        self.status_label.text = 'Status: Standing'
        if self.requests:
            self.process_next_request()

    # Método para regresar a la pantalla de agregar solicitudes
    def go_to_request(self, instance):
        self.manager.current = 'request'

# Administración de las diferentes pantallas
class ElevatorApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MaintenanceScreen(name='maintenance'))
        sm.add_widget(RequestScreen(name='request'))
        sm.add_widget(ElevatorScreen(name='elevator'))
        return sm

# Ejecutar la aplicación
if __name__ == '__main__':
    ElevatorApp().run()
