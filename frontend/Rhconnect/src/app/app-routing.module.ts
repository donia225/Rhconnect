import { LOCALE_ID, NgModule } from '@angular/core';
import { registerLocaleData } from '@angular/common';
import localeFr from '@angular/common/locales/fr';
import { Routes, RouterModule } from '@angular/router';
import { AdminComponent } from './theme/layout/admin/admin.component';
import { AccueilComponent } from './theme/layout/accueil/accueil.component';
import LoginComponent from './authentication/login/login.component';
import { RegisterComponent } from './authentication/register/register.component';
import { AuthGuard } from './services/auth/auth.guard';
import { DashboardComponent } from './theme/layout/admin/dashboard/dashboard.component';
import { AjoutOffreComponent } from './theme/layout/admin/recruteur/offres/ajout-offre/ajout-offre.component';
import { ListeOffreComponent } from './theme/layout/admin/recruteur/offres/liste-offre/liste-offre.component';
import { ModifierOffreComponent } from './theme/layout/admin/recruteur/offres/modifier-offre/modifier-offre.component';
import { AboutComponent } from './theme/layout/accueil/about/about.component';
import { OffresComponent } from './theme/layout/accueil/offres/offres.component';
import { NavbarComponent } from './theme/layout/accueil/navbar/navbar.component';
import { PublicLayoutComponent } from './theme/layout/public-layout/public-layout.component';
import { MescandidaturesComponent } from './theme/layout/accueil/candidat/mescandidatures/mescandidatures.component';
import { MonProfilComponent } from './theme/layout/accueil/candidat/mon-profil/mon-profil.component';
import { ResetPasswordComponent } from './authentication/reset-password/reset-password.component';
import { EmployeListComponent } from './theme/layout/admin/gestionnaire/employe-list/employe-list.component';
import { SuiviCarriereComponent } from './theme/layout/admin/gestionnaire/suivi-carriere/suivi-carriere.component';
import { EmployeProfilComponent } from './theme/layout/employe/employe-profil/employe-profil.component';
import { EmployeLayoutComponent } from './theme/layout/employe/employe-layout/employe-layout.component';
import { SidebarEmployeComponent } from './theme/layout/employe/sidebar-employe/sidebar-employe.component';
import { NavbarEmployeComponent } from './theme/layout/employe/navbar-employe/navbar-employe.component';
import { RedirectionGuard } from './services/auth/redirection.guard';

registerLocaleData(localeFr);



export const routes: Routes = [
  {
  path: '',
    component: PublicLayoutComponent,
    children: [
      { path: '', component: AccueilComponent },
      { path: 'about', component: AboutComponent },
      { path: 'offres', component: OffresComponent },
      { path: 'mes-candidatures', component: MescandidaturesComponent },
      { path: 'mon-profil', component:MonProfilComponent}

    ]
  },
  {
  path: 'employe',
  component: EmployeLayoutComponent,
  children: [
    { path: 'profil', component: EmployeProfilComponent },
    {path: 'sidebar', component: SidebarEmployeComponent},
    {path: 'navbar', component: NavbarEmployeComponent}
    
  ]
},
  {
    path: 'auth',
    children: [
      { path: 'login', component: LoginComponent },
      { path: 'register', component: RegisterComponent },
      {path: 'reset-password', component:ResetPasswordComponent},
      { path: 'reset-password/:uid/:token', component: ResetPasswordComponent },
    ]
  },
  {
    path: 'admin',
    canActivate: [AuthGuard],
    component: AdminComponent,
    children: [
      { path: 'dashboard', component: DashboardComponent },
      {
        path: 'offres',
        children: [
          { path: 'ajout', component: AjoutOffreComponent },
          { path: 'liste', component: ListeOffreComponent },
          { path: '', redirectTo: 'liste', pathMatch: 'full' },
          { path:'modifier/:id', component: ModifierOffreComponent },
        ]
      },
      {
        path: 'gestion-carriere',
        children: [
          { path: '', component: EmployeListComponent },
          { path: 'suivi/:id', component: SuiviCarriereComponent }
        ]
      },
      
      {path: 'logo', loadComponent: () => import('./theme/layout/admin/navigation/nav-logo/nav-logo.component').then((c) => c.NavLogoComponent) },
      { path: 'navbar', loadComponent: () => import('./theme/layout/admin/nav-bar/nav-bar.component').then((c) => c.NavBarComponent) },
      {path:'navright', loadComponent: () => import('./theme/layout/admin/nav-bar/nav-right/nav-right.component').then((c) => c.NavRightComponent) }, 
      { path: 'sidebar', loadComponent: () => import('./theme/layout/admin/sidebar/sidebar.component').then((c) => c.SidebarComponent) },
      
    
      

    ]
  }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule],
  providers: [
  { provide: LOCALE_ID, useValue: 'fr-FR' }
],

})
export class AppRoutingModule {}
