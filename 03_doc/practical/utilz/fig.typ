#import "@preview/cetz:0.5.2"

#set page(width: auto, height: auto, margin: 5mm, fill: luma(245))
#set text(lang: "fr", fill: black)

#let c_grad_1 = rgb("#ccebf6")
#let c_grad_2 = rgb("#56a6c1")
#let c_grad_3 = rgb("#0c6e8f")
#let c_rect_1 = rgb("#F7DAE5")
#let c_rect_2 = rgb("#FFF2E1")
#let c_rect_3 = rgb("#C3E2E6")
#let c_rect_4 = rgb("#D0CCE0")

#let sf = 0.75

#let drawing = align(center)[
  #cetz.canvas(length: 1.2cm * sf, {
    import cetz.draw: *
    
    // Axes
    line((0, 0), (10, 0), mark: (end: ">"), stroke: black, fill: black)
    content((9.5, -0.4), text(font: "Libertinus Sans", size: 16pt * sf)[$x$])
    line((0, 0), (0, 10), mark: (end: ">"), stroke: black, fill: black)
    content((-0.4, 9.5), text(font: "Libertinus Sans", size: 16pt * sf)[$y$])

    // Background Rectangle
    on-layer(-1, {
      line((0, 0), (0, 10), (10, 10), (10,0), close: true, fill: gradient.linear(
        angle: 40deg,
        (c_grad_1, 0%),
        (c_grad_2, 60%),
        (c_grad_3, 100%)),
        stroke: none)
    })

    // Stations
    circle((1, 5), radius: 0.08, fill: black, name: "S1")
    circle((5, 9), radius: 0.08, fill: black, name: "S2")
    circle((9, 5), radius: 0.08, fill: black, name: "S3")
    circle((5, 1), radius: 0.08, fill: black, name: "S4")
    
    // Labels des stations
    content("S1", text(font: "Libertinus Sans", size: 16pt * sf)[S1], anchor: "east", padding: 0.2)
    content("S2", text(font: "Libertinus Sans", size: 16pt * sf)[S2], anchor: "south", padding: 0.2)
    content("S3", text(font: "Libertinus Sans", size: 16pt * sf)[S3], anchor: "west", padding: 0.2)
    content("S4", text(font: "Libertinus Sans", size: 16pt * sf)[S4], anchor: "north", padding: 0.2)
    
    // Lignes entre les stations
    line("S1", "S2", stroke: black + (1pt * sf))
    line("S2", "S3", stroke: black + (1pt * sf))
    line("S3", "S4", stroke: black + (1pt * sf))
    line("S4", "S1", stroke: black + (1pt * sf))

    //grad rho
    content((5, 5), text(font: "Libertinus Sans", size: 16pt * sf)[$arrow(nabla) rho$])

    // cmap
    on-layer(-1, {
      rect((10.5, 0), (11, 10), fill: gradient.linear(
        angle: 90deg,
        (c_grad_1, 0%),
        (c_grad_2, 60%),
        (c_grad_3, 100%)),
        stroke: black + (0.5pt * sf))
    })
    content((11.4, 5), text(font: "Libertinus Sans", size: 16pt * sf)[$rho$])

    // Flèche vers le bas
    content((5, -0.6), text(font: "Libertinus Sans", size: 24pt * sf)[$arrow.b$])

    let draw-subtriangle(p1, p2, p3, label1, label2, label3, fill_color, center_pos, t_name) = {
      line(p1, p2, p3, close: true, fill: fill_color, stroke: black + (0.5pt * sf))
      content(center_pos, text(font: "Libertinus Sans", size: 16pt * sf)[#t_name])
    }

    draw-subtriangle((1.0, -5.5), (5.0, -1.5), (9.0, -5.5), "S1", "S2", "S3", c_rect_1, (5.0, -4.2), "T1")
    draw-subtriangle((1.0, -6.5), (5.0, -10.5), (9.0, -6.5), "S1", "S4", "S3", c_rect_2, (5.0, -7.8), "T2")
    draw-subtriangle((0.0, -6.0), (4.0, -10.0), (4.0, -2.0), "S1", "S4", "S2", c_rect_3, (2.6, -6.0), "T3")
    draw-subtriangle((10.0, -6.0), (6.0, -10.0), (6.0, -2.0), "S3", "S4", "S2", c_rect_4, (7.4, -6.0), "T4")

  })
]

#drawing