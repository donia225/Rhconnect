import { Component } from '@angular/core';
import { SidebarEmployeComponent } from '../sidebar-employe/sidebar-employe.component';
import { NavbarEmployeComponent } from '../navbar-employe/navbar-employe.component';
import { RouterModule } from '@angular/router';

@Component({
  selector: 'app-employe-layout',
  imports: [SidebarEmployeComponent, NavbarEmployeComponent, RouterModule],
  templateUrl: './employe-layout.component.html',
  styleUrl: './employe-layout.component.scss'
})
export class EmployeLayoutComponent {

}
