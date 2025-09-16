import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { EmployeService } from 'src/app/services/employe/employe.service';

type PlanRow = { libelle: string; delai: string | null; evaluation_fin_cycle: string };

@Component({
  selector: 'app-employe-list',
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './employe-list.component.html'
})
export class EmployeListComponent implements OnInit {
  employes: any[] = [];
  selectedEmploye: any = null;
  suivis: any[] = [];
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

  suiviForm: {
    ancien_poste: string;
    nouveau_poste: string;
    date_changement: string;
    est_promotion: boolean;
    commentaire: string;
    notes: Record<string, number | null>;
    objectifs_plan: PlanRow[];
  } = this.blankForm();

  constructor(private employeService: EmployeService) {}

  ngOnInit() {
    this.loadEmployes();
    this.employeService.reload$.subscribe(() => this.loadEmployes());
  }

  private blankForm() {
    return {
      ancien_poste: '',
      nouveau_poste: '',
      date_changement: '',
      est_promotion: false,
      commentaire: '',
      notes: {
        technique: null,
        communication: null,
        performance: null,
        travail_d_equipe: null,
        leadership: null
      } as Record<string, number | null>,
      objectifs_plan: [] as PlanRow[]
    };
  }

  loadEmployes() {
    this.employeService.getEmployes().subscribe((data: any) => (this.employes = data));
  }

  getNoteValue(key: string): number | null {
    return this.suiviForm.notes[key] ?? null;
  }
  setNoteValue(key: string, value: any) {
    this.suiviForm.notes[key] = (value === '' || value == null) ? null : Number(value);
  }

  selectEmploye(emp: any) {
    this.selectedEmploye = emp;
    this.employeService.getSuivis(emp.id).subscribe((data: any) => {
      this.suivis = data.suivi_carriere ?? data;
    });
  }

  ouvrirFormulaire(emp: any) {
    this.selectedEmploye = emp;
    this.changerPosteVisible = false;
    this.suiviForm = this.blankForm();
    this.suiviForm.ancien_poste = emp.poste_actuel;
    // 1 ligne vide par défaut dans le tableau
    this.addPlanRow();
  }

  addPlanRow() {
    this.suiviForm.objectifs_plan.push({ libelle: '', delai: '', evaluation_fin_cycle: '' });
  }
  removePlanRow(i: number) {
    this.suiviForm.objectifs_plan.splice(i, 1);
  }

  ajouterSuivi() {
  // 1) nettoyer les notes (ne pas comparer à '')
  const notes: Record<string, number> = {};
  Object.keys(this.suiviForm.notes || {}).forEach((k: string) => {
    const v = this.suiviForm.notes[k]; // v: number | null
    if (v !== null && v !== undefined) {
      notes[k] = Number(v);
    }
  });

  // 2) sérialiser le plan dans le commentaire (backend actuel)
  const rows = (this.suiviForm.objectifs_plan || [])
    .filter(r => (r.libelle || '').trim());

  let commentaire = (this.suiviForm.commentaire || '').trim();
  if (rows.length) {
    const lines = rows.map(r => {
      const parts = [r.libelle.trim()];
      if (r.delai) parts.push(`Délai: ${r.delai}`);
      if (r.evaluation_fin_cycle) parts.push(`Évaluation: ${r.evaluation_fin_cycle}`);
      return `- ${parts.join(' | ')}`;
    });
    commentaire = `${commentaire}\n\n[Fixation des objectifs]\n${lines.join('\n')}`.trim();
  }


    const payload: any = {
      employe: this.selectedEmploye.id,
      est_promotion: !!this.suiviForm.est_promotion,
      commentaire,
      notes
      // ⬇️ Quand tu ajoutes le champ côté API, dé-commente :
      // objectifs_plan: rows
    };
    if (this.changerPosteVisible && this.suiviForm.nouveau_poste?.trim()) {
  payload.ancien_poste = this.suiviForm.ancien_poste || null;
  payload.nouveau_poste = this.suiviForm.nouveau_poste.trim();
  payload.date_changement = this.suiviForm.date_changement || null;
}

    this.employeService.ajouterSuivi(payload).subscribe({
      next: () => {
        alert('Suivi ajouté avec succès.');
        this.selectEmploye(this.selectedEmploye); // refresh
      },
      error: (err) => {
        console.error(err);
        alert('Erreur lors de l’ajout.');
      }
    });
  }
}
