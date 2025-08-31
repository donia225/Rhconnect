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
  
NOTE_LABELS: Record<string, string> = {
    technique: 'Technique',
    communication: 'Communication',
    performance: 'Performance',
    travail_d_equipe: "Travail d'équipe",
    leadership: 'Leadership',
    qualite: 'Qualité',
    respect_delais: 'Respect des délais',
    autonomie: 'Autonomie',
    initiative: 'Initiative / Innovation',
    orientation_client: 'Orientation client',
    assiduite: 'Assiduité',
    gestion_stress: 'Gestion du stress',
    securite_conformite: 'Sécurité & conformité',
    apprentissage: 'Apprentissage',
    fiabilite: 'Fiabilité'
  };

   suiviForm: any = {
    ancien_poste: '',
    nouveau_poste: '',
    date_changement: '',
    est_promotion: false,
    commentaire: '',
    objectifs: <string[]>[],
    notes: {
      technique: null,
      communication: null,
      performance: null,
      travail_d_equipe: null,
      leadership: null
    },
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
getNoteValue(key: string): number | null {
  return this.suiviForm.notes[key] ?? null;
}
setNoteValue(key: string, value: any) {
  this.suiviForm.notes[key] = (value === '' || value == null) ? null : Number(value);
}


 selectEmploye(emp: any) {
    this.selectedEmploye = emp;
    this.ajoutVisible = false;
    this.employeService.getSuivis(emp.id).subscribe((data: any) => {
      // data = { employe: {...}, suivi_carriere: [...] } d'après le serializer
      this.suivis = data.suivi_carriere ?? data;
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
      commentaire: '',
      objectifs: [],
      notes: {
        technique: null,
        communication: null,
        performance: null,
        travail_d_equipe: null,
        leadership: null
      },
      
    };
  }
   addObjectif() {
    this.suiviForm.objectifs.push('');
  }
  removeObjectif(i: number) {
    this.suiviForm.objectifs.splice(i, 1);
  }

ajouterSuivi() {
    // Nettoyage des notes nulles et objectifs vides
    const notes: any = {};
    Object.keys(this.suiviForm.notes || {}).forEach(k => {
      const v = this.suiviForm.notes[k];
      if (v !== null && v !== undefined && v !== '') notes[k] = Number(v);
    });
    const objectifs = (this.suiviForm.objectifs || []).map((s: string) => s.trim()).filter(Boolean);

    const payload = {
      employe: this.selectedEmploye.id,
      ancien_poste: this.suiviForm.ancien_poste || null,
      nouveau_poste: this.suiviForm.nouveau_poste,
      date_changement: this.suiviForm.date_changement,
      est_promotion: !!this.suiviForm.est_promotion,
      commentaire: this.suiviForm.commentaire || '',
      objectifs,
      notes,
      autres_commentaires: this.suiviForm.autres_commentaires || ''
    };

    this.employeService.ajouterSuivi(payload).subscribe({
      next: () => {
        alert('Suivi ajouté avec succès.');
        // Recharge les suivis de l’employé sélectionné
        this.selectEmploye(this.selectedEmploye);
      },
      error: (err) => {
        console.error(err);
        alert('Erreur lors de l’ajout.');
      }
    });
  }



}
