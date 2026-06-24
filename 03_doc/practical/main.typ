#import "@preview/cetz:0.5.2"
#import "utilz/layout.typ": *
#import "utilz/fig.typ": *
#import "@preview/mannot:0.3.1": *
#import "@preview/codly:1.3.0": *
#import "@preview/codly-languages:0.1.1": *
#show: codly-init.with()

#show: doc => conf(
  doc,
)

= Physical Oceanography Lab

== Seabird - Analyzing and Visualizing CTD Data

Start by copying the following files to your working directory:
- Raw data (e.g., `20090610a.hex`)
- The configuration file (e.g., `20090610a.CON`)
- The program setup file for the process you are about to use (e.g., `atCnv.psa`)

These files can all be found in `toulouse/Seabird`. Once copied, you can process the data directly in your working directory.

In the Seabird interface, you need to set up pathnames and options. To run a process (e.g., "filter"):
+ Open the `.psa` file that you have copied to your workspace: *OPEN `filter.psa`*
+ Select your input file: *SELECT `<last_file_you_worked_on>.cnv`*
+ Select the output directory: *SELECT* your workspace, append `_filter`, and keep the rest of the output filename the same as the input filename.

#rect(fill: luma(245), inset: 10pt, radius: 4pt)[
  *Note:* In each case, make sure the path name to your working file correctly points to your working directory!
]

When the setup is ready, click *START PROCESS*.

Most of the processes will take a file like `myfile.cnv` and add your appendix to create, for example, `myfile_filter.cnv`. This way, you keep a different file for each stage of the process.

- The first program to run is `datcnv`, which takes `myfile.hex` and creates `myfile.cnv`.
- At any time, you can look at a file using Notepad (Right-click $->$ Open with $->$ Notepad). You can use this to edit files, too.

#rect(fill: luma(245), inset: 10pt, radius: 4pt)[
  *Important:* Do not double-click on a `.cnv` file! Windows will open it with an inappropriate program.
]

At any time, you can also use *Sea Plot* to visualize the results.

#pagebreak()

== Calculating the geostrophic velocity

The objective of this section is to determine the geostrophic velocity (GEOVEL) of the water column based on the CTD measurements.

*Calculations:*

#align(center)[
#rect(fill: luma(245), width: 100%)[
#figure(
  drawing,
  caption: [Decomposition of the 4-station (S) array into triangles (T) for horizontal density gradient calculation.]
)<flat_projection>]]

// // this illustration is compiled in another document so it doesn't take all the memory of this one 
// #align(center)[
//   #rect(fill: luma(245), width: 100%)[
//     #figure(
//       image("GEOVEL_sphere_view.png", width: 40%),
//       caption: [Projection of the boat's coordinates on the geographic reference frame.]
//     )<sphere_projection>
//   ]
// ]

The local density plane equation applied to each triangle at every depth in @flat_projection is:
$ rho(x,y) = rho_1 + frac(partial rho, partial x) x + frac(partial rho, partial y) y $

By knowing the coordinates and the measured density at the three stations of a given triangle, we solve this system numerically for each depth layer. This yields the constant horizontal density gradients for that specific triangle:
$ nabla rho = (frac(partial rho, partial x), frac(partial rho, partial y)) $

By differentiating the #highlight(fill: green.lighten(80%))[geostrophic equation] with respect to depth and substituting the #highlight(fill: red.lighten(80%))[hydrostatic pressure gradient], we obtain the #highlight(fill: blue.lighten(80%))[vertical shear of the geostrophic velocity]:

$
  markrect(rho_0 f arrow(v) &= hat(k) times nabla p, outset: #0.2em, color: #green.lighten(80%), fill: #green.lighten(80%)) \
  frac(partial, partial z)(rho_0 f arrow(v)) &= frac(partial, partial z) (hat(k) times nabla p) \
  markrect(frac(partial p, partial z) &= - rho g, outset: #0.2em, color: #red.lighten(80%), fill: #red.lighten(80%)) \
  rho_0 f frac(partial arrow(v), partial z) &= hat(k) times nabla frac(partial p, partial z) \
  markrect(rho_0 f frac(partial arrow(v), partial z) &= - g hat(k) times nabla rho, outset: #0.2em, color: #blue.lighten(80%), fill: #blue.lighten(80%))
$

Integrating this relation over the water column (from the surface $0$ to depth $z$) yields the velocity profile:
$
  integral^z_0 frac(partial arrow(v), partial z) dif z &= -frac(g, rho_0 f) hat(k) times integral^z_0 nabla rho dif z \
  markrect(arrow(v)(z) - arrow(v)_s &= -frac(g, rho_0 f) hat(k) times integral^z_0 nabla rho dif z, outset: #0.2em, color: #luma(245), fill: #luma(245))
$

Because the horizontal density gradient varies with depth, the integral is computed numerically as a discrete sum over $n$ depth layers of thickness $Delta z_i$:
$
integral^(z_n)_0 nabla rho dif z approx sum_(i=1)^n nabla rho(z_i) Delta z_i
$

Applying the cross product to this sum:
$
- hat(k) times sum_(i=1)^n nabla rho(z_i) Delta z_i &= - vec(0, 0, 1) times sum_(i=1)^n vec(frac(partial rho, partial x)(z_i), frac(partial rho, partial y)(z_i), 0) Delta z_i \
&= sum_(i=1)^n vec(frac(partial rho, partial y)(z_i), - frac(partial rho, partial x)(z_i), 0) Delta z_i
$

Finally, the geostrophic velocity components for a given triangle at depth level $z_n$ are:
$
cases(
  v_x (z_n) - v_(s,x) &=  frac(g, rho_0 f) sum_(i=1)^n frac(partial rho, partial y)(z_i) Delta z_i,
  v_y (z_n) - v_(s,y) &= -frac(g, rho_0 f) sum_(i=1)^n frac(partial rho, partial x)(z_i) Delta z_i
)
$

*Manipulations:*

Open a `miniconda3` terminal and run the commands :

#codly(languages: codly-languages)
```conda
conda activate GEOVEL
cd path/to/geovel/folder
python run main.py
```