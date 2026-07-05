extends Node2D
var rects: Array = []
var circles: Array = []

func _ready() -> void:
    queue_redraw()

func _draw() -> void:
    var fill := Color(0.85, 0.18, 0.12, 0.20)
    var line := Color(1.0, 0.28, 0.18, 0.95)
    for d in rects:
        var size := Vector2(d[2], d[3])
        var rect := Rect2(Vector2(d[0], d[1]) - size * 0.5, size)
        draw_rect(rect, fill, true)
        draw_rect(rect, line, false, 2.0)
    for d in circles:
        var center := Vector2(d[0], d[1])
        draw_circle(center, d[2], fill)
        draw_arc(center, d[2], 0.0, TAU, 48, line, 2.0)
