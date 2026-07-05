extends Node2D
## Text-only GitHub build of the Bree-land map for Godot 4.2+.
## F3 shows every collider: no unexplained invisible walls.

const WORLD_SIZE := Vector2(2560, 1440)
const SPEED := 250.0
var player: CharacterBody2D
var camera: Camera2D
var debug_shapes: Node2D
var location_label: Label
var show_debug := false

const HOUSES := [
    [840,800,48,32],[884,910,44,30],[930,764,48,34],[1080,780,50,34],
    [1150,910,44,30],[1060,950,44,32],[960,960,40,28],[1110,700,40,28],
    [850,720,38,28],[1030,810,72,50],[1380,780,40,28],[1440,820,44,30],
    [1490,760,40,28],[1360,860,36,26],[1510,860,38,26],[1480,490,46,32],
    [1540,510,40,28],[1580,450,40,28],[1440,540,36,26],[1710,240,42,30],
    [1770,270,40,28],[1810,216,36,26],[1684,300,36,26]
]
const BLOCKED_GROVES := [[1240,170,70],[1390,145,64],[1540,160,62],[1910,190,68],[1120,310,58],[1290,330,54],[1700,370,64],[1980,350,70],[1880,520,62],[2100,460,66]]
const DEEP_POOLS := [[2200,970,42],[2320,1100,46],[2140,1220,38],[2420,900,35]]
const LOCATIONS := [
    [Rect2(760,650,480,420),"Бри"],[Rect2(1280,690,420,350),"Стэддл"],
    [Rect2(1360,360,360,300),"Комб"],[Rect2(1580,120,360,300),"Арчет"],
    [Rect2(980,80,1160,600),"Четвуд"],[Rect2(1780,660,760,760),"Миджуотерские топи"],
    [Rect2(500,1080,1300,340),"Южные холмы"],[Rect2(0,760,2560,180),"Великая Восточная дорога"]
]

func _ready() -> void:
    var map := Sprite2D.new()
    map.texture = load("res://assets/maps/bree_lands_world.svg")
    map.centered = false
    map.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
    map.z_index = -10
    add_child(map)
    _make_collisions()
    _make_player()
    _make_ui()
    _make_debug()

func _make_collisions() -> void:
    var body := StaticBody2D.new()
    body.name = "VisibleObstacles"
    add_child(body)
    for h in HOUSES:
        _rect_shape(body, Vector2(h[0], h[1]), Vector2(h[2], h[3]))
    for c in BLOCKED_GROVES + DEEP_POOLS:
        var shape := CircleShape2D.new()
        shape.radius = c[2]
        var node := CollisionShape2D.new()
        node.position = Vector2(c[0], c[1])
        node.shape = shape
        body.add_child(node)
    var bounds := StaticBody2D.new()
    add_child(bounds)
    _rect_shape(bounds, Vector2(1280,-16), Vector2(2560,32))
    _rect_shape(bounds, Vector2(1280,1456), Vector2(2560,32))
    _rect_shape(bounds, Vector2(-16,720), Vector2(32,1440))
    _rect_shape(bounds, Vector2(2576,720), Vector2(32,1440))

func _rect_shape(parent: Node, center: Vector2, size: Vector2) -> void:
    var shape := RectangleShape2D.new()
    shape.size = size
    var node := CollisionShape2D.new()
    node.position = center
    node.shape = shape
    parent.add_child(node)

func _make_player() -> void:
    player = CharacterBody2D.new()
    player.position = Vector2(650,860)
    var collision := CollisionShape2D.new()
    var capsule := CapsuleShape2D.new()
    capsule.radius = 10
    capsule.height = 28
    collision.shape = capsule
    player.add_child(collision)
    var body := Polygon2D.new()
    body.polygon = PackedVector2Array([Vector2(0,-17),Vector2(11,-3),Vector2(8,13),Vector2(-8,13),Vector2(-11,-3)])
    body.color = Color("d9c183")
    player.add_child(body)
    var cloak := Polygon2D.new()
    cloak.polygon = PackedVector2Array([Vector2(0,-10),Vector2(9,12),Vector2(-9,12)])
    cloak.color = Color("4c6f3f")
    cloak.z_index = 1
    player.add_child(cloak)
    add_child(player)
    camera = Camera2D.new()
    camera.zoom = Vector2(1.35,1.35)
    camera.position_smoothing_enabled = true
    camera.position_smoothing_speed = 7
    camera.limit_right = 2560
    camera.limit_bottom = 1440
    player.add_child(camera)

func _make_ui() -> void:
    var ui := CanvasLayer.new()
    add_child(ui)
    var panel := ColorRect.new()
    panel.position = Vector2(18,18)
    panel.size = Vector2(390,82)
    panel.color = Color(0.08,0.09,0.07,0.84)
    ui.add_child(panel)
    location_label = Label.new()
    location_label.position = Vector2(32,28)
    location_label.add_theme_font_size_override("font_size",24)
    location_label.text = "Земли Бри"
    ui.add_child(location_label)
    var hint := Label.new()
    hint.position = Vector2(32,62)
    hint.text = "WASD/стрелки • колесо — масштаб • F3 — коллизии"
    ui.add_child(hint)

func _make_debug() -> void:
    debug_shapes = Node2D.new()
    debug_shapes.set_script(load("res://scripts/CollisionDebug.gd"))
    debug_shapes.set("rects", HOUSES)
    debug_shapes.set("circles", BLOCKED_GROVES + DEEP_POOLS)
    debug_shapes.visible = false
    debug_shapes.z_index = 50
    add_child(debug_shapes)

func _physics_process(_delta: float) -> void:
    var v := Vector2.ZERO
    if Input.is_key_pressed(KEY_A) or Input.is_key_pressed(KEY_LEFT): v.x -= 1
    if Input.is_key_pressed(KEY_D) or Input.is_key_pressed(KEY_RIGHT): v.x += 1
    if Input.is_key_pressed(KEY_W) or Input.is_key_pressed(KEY_UP): v.y -= 1
    if Input.is_key_pressed(KEY_S) or Input.is_key_pressed(KEY_DOWN): v.y += 1
    player.velocity = v.normalized() * SPEED
    player.move_and_slide()
    location_label.text = "Земли Бри"
    for data in LOCATIONS:
        if data[0].has_point(player.position):
            location_label.text = data[1]
            break

func _unhandled_input(event: InputEvent) -> void:
    if event is InputEventKey and event.pressed and not event.echo and event.keycode == KEY_F3:
        show_debug = not show_debug
        debug_shapes.visible = show_debug
    elif event is InputEventMouseButton and event.pressed:
        var value := camera.zoom.x
        if event.button_index == MOUSE_BUTTON_WHEEL_UP: value *= 1.12
        if event.button_index == MOUSE_BUTTON_WHEEL_DOWN: value /= 1.12
        value = clampf(value,0.8,2.4)
        camera.zoom = Vector2(value,value)
