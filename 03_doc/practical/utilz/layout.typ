#let conf(doc) = {

      // pagebreak()
      set page(numbering: "1", number-align: right)
      set text(fill: black, size: 13pt, lang: "en", hyphenate: true)
      set par(justify: true, linebreaks: "optimized")
      counter(page).update(1)
      
      set page(
        fill: none,
        margin: (top: 3cm, right: 2.6cm, left: 2.6cm, bottom: 3cm),
        header: [
          #v(30pt)
          #grid(
              columns: (1fr, 1fr, 1fr),
              align: (left + horizon, center + horizon, right + horizon),
              
              text(fill: gray, size: 10pt)[Physical Oceanography Lab],
              text(fill: gray, size: 10pt)[],
              text(fill: gray, size: 10pt)[M1 SOAC - Banyuls-sur-Mer],
            )
          #line(length: 100%, stroke: 0.25pt + gray)
        ],
      )
      
      set heading(numbering:none)
      show heading.where(level: 1): set text(size: 16pt)
      show heading.where(level: 2): set text(size: 16pt)

      set figure(supplement: [Figure])
      show figure.caption: emph
      show figure.where(kind: table): set figure(supplement: [Tableau])

      // set math.equation(numbering: "(1)")
      set math.equation(supplement: "Équation")
      show math.equation: it => {
        show ".": math.class("normal")[,]
        it
      }

      set math.vec(gap: 1.3em)
      set math.cases(gap: 1.3em)
      
      show ref: it => underline(text(blue, it))
      show ref: it => {
        let el = it.element

        if el != none and it.supplement == auto {
          
          if el.func() == figure {
            let supp = if el.kind == table { "tableau" } else { "figure" }
            
            return ref(it.target, supplement: supp)
            
          } else if el.func() == math.equation {
            return ref(it.target, supplement: "équation")
          } else if el.func() == heading {
            return ref(it.target, supplement: "chapitre")
          }
        }
    
        it
      }
          
      doc

}