// geovel
// 
// Calcul de la vitesse geostrophique 
// 
//
// 19 Mai 2009 -EK 
//
// =========================================================================
// 20 Sept 2016 -EK : Modification des commandes pour les plots
// see https://help.scilab.org/docs/6.0.0/en_US/axes_properties.html
//
// ex: pour renverser axe Y, set(gca, 'Ydir', 'Reverse') ne fonctionne plus:
// fig1 = gca();
// fig1.axes_reverse = ["on", "off"]
//
// autre exemple: hold on remplacer par set(gca(),"auto_clear","off");
// =========================================================================
//
//
// Input: tem (in situ ou potentielle), sal, depth, lat, lon

// ---  user defined parameters to edit in the code ---------------

pres_ref = 50;

filename1='Station_C_Est.cnv'
statione=read(filename1,-1,6)
pres1 = statione(:,1);
tem1 = statione(:,2);
sal1 = statione(:,6);
clear statione

filename2='Station_B_Ouest.cnv'
stationf=read(filename2,-1,6)
pres2 = stationf(:,1);
tem2 = stationf(:,2);
sal2 = stationf(:,6);
clear stationf

// Position station en deg decimal
// ex: lat1 = 16 20.120 S  ==> 16,(20.120/60): 16.3333
lat1 = 42.4817; 
lon1 = 3.1979;  
lat2 = 42.4815; 
lon2 = 3.1755;  

// ----- end of user defined parameters -------------------------------

// recherche des profondeurs communes
// [pres ia ib] = [intersect(pres1, pres2)]'; // version Windows
[pres ia ib] = [intersect(pres1, pres2)];   // version Linux
tem = [tem1(ia) tem2(ib)];
sal = [sal1(ia) sal2(ib)];
clear ia ib

lon = [lon1 lon2];
lat = [lat1 lat2];

nsta = 2;
nz = length(pres);
pres2 = [pres' pres'];
 
// Changement profondeur m ==> pression db
//depth_all = repmat(depth, [1 ny]);
//lat_all = repmat(lat, [1 nz])';
//pres_all = sw_pres(depth_all,lat_all);
//pres_all2 = pres_all;
//pres_all2 = repmat(pres_all2, [1 1 nx]);

// Conversion temperature potentielle ==> temperature in-situ
//ptem = tem; clear tem;
//tem = sw_temp(sal,ptem,pres_all2,0*pres_all2);

// Volume specifique
// Routine "perso", attention unite 1e-8*m3/kg
// [sv sig] = svan(sal,tem,pres_all2);  // unites 1e-8*m3/kg
// Routine "seawater", attention unites m3/kg

exec sw_svan.sci;
sv = sw_svan(sal,tem,pres2);

dp=diff(pres)';
dp2=[dp,dp];


// Hauteur dynamique 
// H(p) - H(pref) = -integrale(svan*dp)
// pression a convertir en Pa => 1 bar = 1e5 Pa soit 1dbar = 1e4 Pa
//
dynht1_unref= cumsum(0.5*(sv(1:nz-1,:) + sv(2:nz,:)).* dp2*1e4,1);
//
// dernier niveau (a zero)
dynht1_unref = [zeros(1,nsta); dynht1_unref];

// Attention ici dynht1_unref est le cumul de 0 a p, or normalement 
// c'est l'integrale de p a 0 (avec dp>0) donc changement de signe:
dynht1_unref = -dynht1_unref;

// Niveau de reference
ind_ref = find(pres_ref==pres)
//dynht1_ref = squeeze(dynht1_unref(ind_ref,:));
dynht1_ref = dynht1_unref(ind_ref,:);
//dynht1_ref = repmat(dynht1_ref', [1 nz])';
dynht1_all=[dynht1_ref(1)*ones(nz,1) dynht1_ref(2)*ones(nz,1)];

// Hauteur dynamique par rapport au niveau de reference
// si besoin: changement d'unite: m2s-2 --> dyn.m=H/10 --> dyn.cm=H*100/10=H*10
// soit facteur 10 entre m2s-2 et dyn.cm
dynht1 = dynht1_unref - dynht1_all;

// Transformation du masque pour les latitudes
j1 = 2:nsta;
j0 = 1:(nsta-1);

pi=3.141592654
// Cas ug = - 1/f * DH/Dy  Attention non valable a l'Equateur
Omega = 7.27e-5 ;
// f is 2*Omega*sin(Theta).
f = 2*Omega*sin(pi/180*0.5*(lat(j0)+lat(j1))) ;

exec sw_dist.sci
dist2m = 1000*sw_dist(lat,lon,'km')

fds = f .* dist2m;
ffds = fds(:,ones(1,nz))';

// fu = - dD/dy; fv = dD/dx  sans correction meridionale.
ug_nocor = -(dynht1(:,j1) - dynht1(:,j0))./ffds;

// m/s ==> cm/s
fact = 100;
ug_nocor = fact*ug_nocor;

figure;
plot(ug_nocor, -pres, '-'); 
plot(ug_nocor, -pres, '.');

set(gca(),"auto_clear","off");

//fig1 = gca();
//fig1.axes_reverse = ["off", "on"];

ylabel('Pression (dbar)');
title('Courant geostrophique (cm/s)');

nsc=ug_nocor
return 


