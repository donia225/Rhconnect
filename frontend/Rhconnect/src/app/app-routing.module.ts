import { NgModule } from '@angular/core';
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
import { ListeCarriereComponent } from './theme/layout/admin/recruteur/gestion-carriere/liste-carriere/liste-carriere.component';
import { AjoutCarriereComponent } from './theme/layout/admin/recruteur/gestion-carriere/ajout-carriere/ajout-carriere.component';
import { AboutComponent } from './theme/layout/accueil/about/about.component';
import { OffresComponent } from './theme/layout/accueil/offres/offres.component';
import { NavbarComponent } from './theme/layout/accueil/navbar/navbar.component';
import { PublicLayoutComponent } from './theme/layout/public-layout/public-layout.component';




export const routes: Routes = [
  {
  path: '',
    component: PublicLayoutComponent,   // Ton layout public avec navbar
    children: [
      { path: '', component: AccueilComponent },
      { path: 'about', component: AboutComponent },
      { path: 'offres', component: OffresComponent },
    ]
  },
  {
    path: 'auth',
    children: [
      { path: 'login', component: LoginComponent },
      { path: 'register', component: RegisterComponent }
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
          { path: '', component: ListeCarriereComponent },
          { path: 'ajout', component: AjoutCarriereComponent }
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
  exports: [RouterModule]
})
export class AppRoutingModule {}
