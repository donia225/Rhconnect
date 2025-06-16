import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { EmployeService } from 'src/app/services/employe/employe.service';


@Component({
  selector: 'app-employe-list',
  imports:[CommonModule],
  templateUrl: './employe-list.component.html'
})
export class EmployeListComponent implements OnInit {
  employes: any[] = [];
  selectedEmploye: any = null;
  suivis: any[] = [];

  constructor(private employeService: EmployeService) {}

  ngOnInit() {
     this.loadEmployes();

  // 👇 Souscrire pour écouter les rechargements demandés
  this.employeService.reload$.subscribe(() => {
    this.loadEmployes();
  });
  }

  loadEmployes() {
    this.employeService.getEmployes().subscribe((data: any) => {
      this.employes = data;
    });
  }

  selectEmploye(emp: any) {
    this.selectedEmploye = emp;
    this.employeService.getSuivis(emp.id).subscribe((data: any) => {
      this.suivis = data;
    });
  }



}
