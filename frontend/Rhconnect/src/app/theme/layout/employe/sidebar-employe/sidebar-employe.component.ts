import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterModule } from '@angular/router';

@Component({
  selector: 'app-sidebar-employe',
  imports: [RouterLinkActive,CommonModule, RouterModule],
  templateUrl: './sidebar-employe.component.html',
  styleUrl: './sidebar-employe.component.scss'
})
export class SidebarEmployeComponent {

}
