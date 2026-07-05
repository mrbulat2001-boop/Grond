extends Node2D

const WORLD_SIZE := Vector2(2400.0, 1600.0)
const SPEED := 270.0
const INTERACT_DISTANCE := 125.0

var player: CharacterBody2D
var world_modulate: CanvasModulate
var location_label: Label
var time_label: Label
var action_label: Label
var dialogue_panel: Panel
var dialogue_label: RichTextLabel
var map_layer: CanvasLayer
var interactables: Array[Node2D] = []
var nearest: Node2D
var minutes := 9 * 60
var map_open := false
var dialogue_open := false

var regions := [
	{"name": "Бри", "center": Vector2(650, 820), "radius": 250.0},
	{"name": "Стэддл", "center": Vector2(1040, 950), "radius": 210.0},
	{"name": "Комб", "center": Vector2(1280, 600), "radius": 190.0},
	{"name": "Арчет", "center": Vector2(1600, 330), "radius": 185.0},
	{"name": "Четвуд", "center": Vector2(1760, 370), "radius": 560.0},
	{"name": "Топи Миджуотер", "center": Vector2(2070, 1160), "radius": 470.0},
	{"name": "Могильники", "center": Vector2(270, 1320), "radius": 330.0}
]

func _ready() -> void:
	_setup_input()
	_build_world()
	_spawn_player()
	_spawn_points()
	_build_ui()
	_update_time()

func _setup_input() -> void:
	_bind("left", [KEY_A, KEY_LEFT])
	_bind("right", [KEY_D, KEY_RIGHT])
	_bind("up", [KEY_W, KEY_UP])
	_bind("down", [KEY_S, KEY_DOWN])
	_bind("interact", [KEY_E, KEY_ENTER])
	_bind("map", [KEY_M])
	_bind("wait", [KEY_T])

func _bind(action: String, keys: Array[int]) -> void:
	if not InputMap.has_action(action):
		InputMap.add_action(action)
	for key: int in keys:
		var event := InputEventKey.new()
		event.physical_keycode = key
		InputMap.action_add_event(action, event)

func _build_world() -> void:
	var map := Sprite2D.new()
	map.texture = load("res://assets/bree_lands_map.svg")
	map.position = WORLD_SIZE * 0.5
	map.z_index = -100
	add_child(map)
	world_modulate = CanvasModulate.new()
	add_child(world_modulate)
	for wall in [
		[Vector2(1200, -30), Vector2(2500, 60)],
		[Vector2(1200, 1630), Vector2(2500, 60)],
		[Vector2(-30, 800), Vector2(60, 1700)],
		[Vector2(2430, 800), Vector2(60, 1700)]
	]:
		var body := StaticBody2D.new()
		body.position = wall[0]
		var shape := CollisionShape2D.new()
		var rect := RectangleShape2D.new()
		rect.size = wall[1]
		shape.shape = rect
		body.add_child(shape)
		add_child(body)

func _spawn_player() -> void:
	player = CharacterBody2D.new()
	player.position = Vector2(410, 850)
	player.z_index = 30
	var body := Polygon2D.new()
	body.polygon = PackedVector2Array([Vector2(0, -22), Vector2(-16, 18), Vector2(16, 18)])
	body.color = Color(0.93, 0.86, 0.65)
	player.add_child(body)
	var outline := Line2D.new()
	outline.points = PackedVector2Array([Vector2(0, -22), Vector2(-16, 18), Vector2(16, 18), Vector2(0, -22)])
	outline.width = 4
	outline.default_color = Color(0.20, 0.16, 0.11)
	player.add_child(outline)
	var collision := CollisionShape2D.new()
	var circle := CircleShape2D.new()
	circle.radius = 17
	collision.shape = circle
	player.add_child(collision)
	var camera := Camera2D.new()
	camera.zoom = Vector2(1.1, 1.1)
	camera.position_smoothing_enabled = true
	camera.position_smoothing_speed = 6.0
	camera.limit_right = int(WORLD_SIZE.x)
	camera.limit_bottom = int(WORLD_SIZE.y)
	player.add_child(camera)
	add_child(player)

func _spawn_points() -> void:
	_spawn_point("Трактир «Гарцующий пони»", Vector2(650, 805), Color(0.78, 0.35, 0.20), "Сердце Бри. Здесь начнётся первая сюжетная цепочка — расследование исчезнувших обозов.")
	_spawn_point("Западные ворота", Vector2(470, 840), Color(0.78, 0.62, 0.30), "Дорога на запад ведёт обратно к Ширу. Это естественный переход из первой игры.")
	_spawn_point("Восточные ворота", Vector2(835, 820), Color(0.78, 0.62, 0.30), "За частоколом начинается тревожная дорога через Четвуд.")
	_spawn_point("Стэддл", Vector2(1040, 950), Color(0.90, 0.72, 0.34), "Дома и огороды поднимаются по склону. Ночью здесь видели незнакомые огни.")
	_spawn_point("Комб", Vector2(1280, 600), Color(0.90, 0.72, 0.34), "Лесничие Комба первыми заметили, что птицы покидают Четвуд.")
	_spawn_point("Арчетская сторожка", Vector2(1600, 330), Color(0.90, 0.72, 0.34), "Крайнее поселение под тяжёлыми кронами. Дальше дорога почти не охраняется.")
	_spawn_point("Кромка Четвуда", Vector2(1450, 480), Color(0.25, 0.60, 0.32), "Под деревьями всегда темнее, чем должно быть.")
	_spawn_point("Старая гать Миджуотера", Vector2(2050, 1100), Color(0.28, 0.68, 0.72), "Доски прогибаются над чёрной водой. Камыши отвечают на шаги с опозданием.")
	_spawn_point("Первый курган", Vector2(280, 1320), Color(0.63, 0.58, 0.72), "Западная кромка Могильников. Пока это граница будущей главы.")

func _spawn_point(title: String, position_value: Vector2, color: Color, text: String) -> void:
	var point := Node2D.new()
	point.position = position_value
	point.z_index = 15
	point.set_meta("title", title)
	point.set_meta("text", text)
	var marker := Polygon2D.new()
	marker.polygon = _circle_points(22, 20)
	marker.color = color
	point.add_child(marker)
	var ring := Line2D.new()
	ring.points = _closed_circle_points(24, 20)
	ring.width = 4
	ring.default_color = Color(0.18, 0.14, 0.09)
	point.add_child(ring)
	var label := Label.new()
	label.text = title
	label.position = Vector2(-90, 28)
	label.size = Vector2(180, 28)
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.add_theme_font_size_override("font_size", 16)
	label.add_theme_color_override("font_color", Color(0.97, 0.92, 0.78))
	label.add_theme_color_override("font_shadow_color", Color(0.05, 0.05, 0.04, 0.95))
	label.add_theme_constant_override("shadow_offset_x", 2)
	label.add_theme_constant_override("shadow_offset_y", 2)
	point.add_child(label)
	add_child(point)
	interactables.append(point)

func _circle_points(radius: float, count: int) -> PackedVector2Array:
	var points := PackedVector2Array()
	for i in range(count):
		var angle := TAU * float(i) / float(count)
		points.append(Vector2(cos(angle), sin(angle)) * radius)
	return points

func _closed_circle_points(radius: float, count: int) -> PackedVector2Array:
	var points := _circle_points(radius, count)
	points.append(points[0])
	return points

func _build_ui() -> void:
	var ui := CanvasLayer.new()
	ui.layer = 20
	add_child(ui)
	var panel := Panel.new()
	panel.position = Vector2(24, 22)
	panel.size = Vector2(570, 120)
	ui.add_child(panel)
	var title := Label.new()
	title.position = Vector2(16, 10)
	title.text = "ЗЕМЛИ БРИ — ПРОТОТИП КАРТЫ"
	title.add_theme_font_size_override("font_size", 22)
	panel.add_child(title)
	location_label = Label.new()
	location_label.position = Vector2(16, 45)
	location_label.add_theme_font_size_override("font_size", 19)
	panel.add_child(location_label)
	time_label = Label.new()
	time_label.position = Vector2(16, 76)
	time_label.add_theme_font_size_override("font_size", 18)
	panel.add_child(time_label)
	action_label = Label.new()
	action_label.anchor_left = 0.5
	action_label.anchor_right = 0.5
	action_label.anchor_top = 1.0
	action_label.anchor_bottom = 1.0
	action_label.offset_left = -390
	action_label.offset_right = 390
	action_label.offset_top = -72
	action_label.offset_bottom = -24
	action_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	action_label.add_theme_font_size_override("font_size", 19)
	ui.add_child(action_label)
	dialogue_panel = Panel.new()
	dialogue_panel.anchor_left = 0.5
	dialogue_panel.anchor_right = 0.5
	dialogue_panel.anchor_top = 1.0
	dialogue_panel.anchor_bottom = 1.0
	dialogue_panel.offset_left = -540
	dialogue_panel.offset_right = 540
	dialogue_panel.offset_top = -270
	dialogue_panel.offset_bottom = -100
	dialogue_panel.visible = false
	ui.add_child(dialogue_panel)
	dialogue_label = RichTextLabel.new()
	dialogue_label.position = Vector2(22, 18)
	dialogue_label.size = Vector2(1036, 135)
	dialogue_label.bbcode_enabled = true
	dialogue_label.add_theme_font_size_override("normal_font_size", 20)
	dialogue_panel.add_child(dialogue_label)
	map_layer = CanvasLayer.new()
	map_layer.layer = 40
	map_layer.visible = false
	add_child(map_layer)
	var shade := ColorRect.new()
	shade.color = Color(0.03, 0.04, 0.025, 0.96)
	shade.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	map_layer.add_child(shade)
	var atlas := TextureRect.new()
	atlas.texture = load("res://assets/bree_lands_map.svg")
	atlas.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	atlas.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	atlas.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	atlas.offset_left = 70
	atlas.offset_right = -70
	atlas.offset_top = 55
	atlas.offset_bottom = -55
	map_layer.add_child(atlas)
	var hint := Label.new()
	hint.text = "АТЛАС ЗЕМЕЛЬ БРИ     M / Esc — закрыть"
	hint.position = Vector2(90, 26)
	hint.add_theme_font_size_override("font_size", 24)
	map_layer.add_child(hint)

func _physics_process(_delta: float) -> void:
	if map_open or dialogue_open:
		player.velocity = Vector2.ZERO
	else:
		player.velocity = Input.get_vector("left", "right", "up", "down") * SPEED
	player.move_and_slide()
	_update_nearest()
	_update_location()

func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("map"):
		map_open = not map_open
		map_layer.visible = map_open
		dialogue_open = false
		dialogue_panel.visible = false
	elif event.is_action_pressed("interact") and not map_open:
		if dialogue_open:
			_close_dialogue()
		elif nearest != null:
			dialogue_open = true
			dialogue_panel.visible = true
			dialogue_label.text = "[b]" + str(nearest.get_meta("title")) + "[/b]\n" + str(nearest.get_meta("text")) + "\n\n[color=#a78d56]E / Esc — закрыть[/color]"
	elif event.is_action_pressed("wait") and not map_open:
		minutes = (minutes + 60) % 1440
		_update_time()
	elif event.is_action_pressed("ui_cancel"):
		if map_open:
			map_open = false
			map_layer.visible = false
		elif dialogue_open:
			_close_dialogue()

func _close_dialogue() -> void:
	dialogue_open = false
	dialogue_panel.visible = false

func _update_nearest() -> void:
	nearest = null
	var best := INTERACT_DISTANCE
	for point: Node2D in interactables:
		var distance := player.position.distance_to(point.position)
		if distance < best:
			best = distance
			nearest = point
	if dialogue_open:
		action_label.text = "E / Esc — закрыть"
	elif nearest != null:
		action_label.text = "E — " + str(nearest.get_meta("title"))
	else:
		action_label.text = "WASD — идти     E — взаимодействие     M — атлас     T — ждать час"

func _update_location() -> void:
	var region_name := "Дикая местность Бри-ланда"
	var best := INF
	for region: Dictionary in regions:
		var center: Vector2 = region.get("center", Vector2.ZERO)
		var radius: float = float(region.get("radius", 0.0))
		var distance := player.position.distance_to(center)
		if distance < radius and distance < best:
			best = distance
			region_name = str(region.get("name", region_name))
	location_label.text = "Место: " + region_name

func _update_time() -> void:
	var hour := int(minutes / 60)
	time_label.text = "Время: %02d:%02d" % [hour, minutes % 60]
	if hour >= 20 or hour < 6:
		world_modulate.color = Color(0.34, 0.43, 0.58)
	elif hour >= 18 or hour < 8:
		world_modulate.color = Color(0.84, 0.72, 0.62)
	else:
		world_modulate.color = Color.WHITE
