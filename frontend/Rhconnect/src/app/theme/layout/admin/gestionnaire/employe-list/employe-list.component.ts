import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { EmployeService } from 'src/app/services/employe/employe.service';


@Component({
  selector: 'app-employe-list',
  imports:[CommonModule, FormsModule, RouterModule],
  templateUrl: './employe-list.component.html'
})
export class EmployeListComponent implements OnInit {
  employes: any[] = [];
  selectedEmploye: any = null;
  suivis: any[] = [];
  ajoutVisible = false;
  changerPosteVisible = false;


  suiviForm = {
    ancien_poste: '',
    nouveau_poste: '',
    date_changement: '',
    est_promotion: false,
    commentaire: ''
  };

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
  this.ajoutVisible = false; // cacher le formulaire si on change d'employé

  this.employeService.getSuivis(emp.id).subscribe((data: any) => {
    this.suivis = data;
  });
}

ouvrirFormulaire(emp: any) {
  this.selectedEmploye = emp;
  this.changerPosteVisible = false;

  this.suiviForm = {
    ancien_poste: emp.poste_actuel,
    nouveau_poste: '',
    date_changement: '',
    est_promotion: false,
    commentaire: ''
  };
}

   ajouterSuivi() {
    const suiviData = {
      ...this.suiviForm,
      employe: this.selectedEmploye.id
    };

    this.employeService.ajouterSuivi(suiviData).subscribe({
      next: () => {
        alert('Suivi ajouté avec succès.');
        this.ajoutVisible = false;
        this.selectEmploye(this.selectedEmploye); // Recharge les suivis
      },
      error: (err) => {
        console.error(err);
        alert('Erreur lors de l’ajout.');
      }
    });
  }


}
