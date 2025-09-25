import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { EmployeService } from 'src/app/services/employe/employe.service';

type PlanRow = { libelle: string; delai: string | null; evaluation_fin_cycle: string };

@Component({
  selector: 'app-employe-list',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './employe-list.component.html',
  styleUrls: ['./employe-list.component.scss']
})
export class EmployeListComponent implements OnInit {
  // Data
  employes: any[] = [];
  filteredEmployes: any[] = [];
  loading = true;

  // Filters
  searchTerm = '';
  selectedDept = '';
  deptOptions: string[] = [];

  // State existant
  selectedEmploye: any = {};
  suivis: any[] = [];
  changerPosteVisible = false;
  addLocked = new Set<number>();
  initialDept = '';
  initialPoste = '';
  modeForm: 'create' | 'edit' = 'create';
  editingSuiviId: number | null = null;

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
    const saved = JSON.parse(localStorage.getItem('addLocked') || '[]') as number[];
    this.addLocked = new Set(saved);
    this.loadEmployes();
    this.employeService.reload$.subscribe(() => this.loadEmployes());
  }

  // ---------- UI helpers ----------
  toUrl(u?: string) {
    if (!u) return '';
    return u.startsWith('http') ? u : `http://127.0.0.1:8000${u}`;
  }
  initials(emp: any) {
    const f = (emp?.user?.first_name || '').trim();
    const l = (emp?.user?.last_name || '').trim();
    return (f[0] || '').toUpperCase() + (l[0] || '').toUpperCase();
  }

  // ---------- Filters ----------
  applyFilters() {
    const q = this.searchTerm.trim().toLowerCase();
    const dept = this.selectedDept;

    this.filteredEmployes = this.employes.filter((e) => {
      const name = `${e?.user?.first_name || ''} ${e?.user?.last_name || ''}`.toLowerCase();
      const poste = (e?.poste_actuel || '').toLowerCase();
      const dpt = (e?.departement || '');
      const matchText = !q || name.includes(q) || poste.includes(q) || dpt.toLowerCase().includes(q);
      const matchDept = !dept || dpt === dept;
      return matchText && matchDept;
    });
  }

  // ---------- Data ----------
  loadEmployes() {
    this.loading = true;
    this.employeService.getEmployes().subscribe({
      next: (data: any[]) => {
        this.employes = Array.isArray(data) ? data : [];
        // options de filtre "département"
        const set = new Set<string>();
        this.employes.forEach(e => { if (e?.departement) set.add(e.departement); });
        this.deptOptions = Array.from(set).sort((a, b) => a.localeCompare(b));
        this.applyFilters();
        this.loading = false;
      },
      error: () => { this.loading = false; }
    });
  }

  // ---------- Form helpers ----------
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
  getNoteValue(key: string): number | null { return this.suiviForm.notes[key] ?? null; }
  setNoteValue(key: string, value: any) { this.suiviForm.notes[key] = (value === '' || value == null) ? null : Number(value); }

  // ---------- Sélection / Suivis ----------
  selectEmploye(emp: any) {
    this.selectedEmploye = emp;
    this.employeService.getSuivis(emp.id).subscribe((data: any) => {
      this.suivis = data.suivi_carriere ?? data ?? [];
    });
  }

  // --- Ouverture modal (création) ---
  ouvrirFormulaire(emp: any) {
    this.modeForm = 'create';
    this.editingSuiviId = null;
    this.selectedEmploye = emp;
    this.initialDept = emp.departement || '';
    this.initialPoste = emp.poste_actuel || '';
    this.changerPosteVisible = false;
    this.suiviForm = this.blankForm();
    this.suiviForm.ancien_poste = emp.poste_actuel;
    this.addPlanRow(); // ligne vide par défaut
  }

  // --- Ouverture modal (édition dernier suivi) ---
  ouvrirEditionDernierSuivi(emp: any) {
    this.modeForm = 'edit';
    this.editingSuiviId = null;
    this.selectedEmploye = emp;
    this.initialDept = emp.departement || '';
    this.initialPoste = emp.poste_actuel || '';
    this.changerPosteVisible = false;

    this.employeService.getSuivis(emp.id).subscribe({
      next: (data: any) => {
        const rows: any[] = (data?.suivi_carriere ?? data ?? []);
        if (!rows.length) { alert('Aucun suivi trouvé pour cet employé.'); return; }
        rows.sort((a, b) => new Date(b.date_changement || 0).getTime() - new Date(a.date_changement || 0).getTime());
        const last = rows[0];
        this.editingSuiviId = last.id;
        this.hydrateFormFromSuivi(last);
      },
      error: () => alert('Erreur lors du chargement des suivis.')
    });
  }

  private hydrateFormFromSuivi(s: any) {
    const notes: Record<string, number | null> = {
      technique: null, communication: null, performance: null, travail_d_equipe: null, leadership: null
    };
    Object.entries(s?.notes || {}).forEach(([k, v]) => {
      const n = typeof v === 'number' ? v : Number(v);
      if (!Number.isNaN(n)) notes[k] = n;
    });

    const plan: PlanRow[] = Array.isArray(s?.objectifs_plan)
      ? s.objectifs_plan.map((r: any) => ({
          libelle: r?.libelle || '',
          delai: r?.delai || '',
          evaluation_fin_cycle: r?.evaluation_fin_cycle || ''
        }))
      : [];

    this.suiviForm = {
      ancien_poste: s?.ancien_poste || (this.selectedEmploye?.poste_actuel || ''),
      nouveau_poste: s?.nouveau_poste || '',
      date_changement: s?.date_changement || '',
      est_promotion: !!s?.est_promotion,
      commentaire: s?.commentaire || '',
      notes,
      objectifs_plan: plan.length ? plan : [{ libelle: '', delai: '', evaluation_fin_cycle: '' }]
    };
  }

  addPlanRow() { this.suiviForm.objectifs_plan.push({ libelle: '', delai: '', evaluation_fin_cycle: '' }); }
  removePlanRow(i: number) { this.suiviForm.objectifs_plan.splice(i, 1); }

  // ---------- Soumission ----------
  onSubmit() { this.modeForm === 'create' ? this.ajouterSuivi() : this.modifierSuivi(); }

  isAddLocked(empId: number | string): boolean { return this.addLocked.has(Number(empId)); }
  private persistLockset() { localStorage.setItem('addLocked', JSON.stringify(Array.from(this.addLocked))); }
  onClickAdd(emp: any) { if (!this.isAddLocked(emp.id)) this.ouvrirFormulaire(emp); }

  ajouterSuivi() {
    const notes: Record<string, number> = {};
    Object.keys(this.suiviForm.notes || {}).forEach((k) => {
      const v = this.suiviForm.notes[k];
      if (v != null) notes[k] = Number(v);
    });

    const objectifs_plan = (this.suiviForm.objectifs_plan || [])
      .filter(r => (r.libelle || '').trim())
      .map(r => ({ libelle: r.libelle.trim(), delai: r.delai || null, evaluation_fin_cycle: (r.evaluation_fin_cycle || '').trim() }));

    const payload: any = {
      employe: this.selectedEmploye.id,
      est_promotion: !!this.suiviForm.est_promotion,
      commentaire: (this.suiviForm.commentaire || '').trim(),
      notes,
      objectifs_plan
    };

    if (this.changerPosteVisible && this.suiviForm.nouveau_poste?.trim()) {
      payload.ancien_poste = this.suiviForm.ancien_poste || null;
      payload.nouveau_poste = this.suiviForm.nouveau_poste.trim();
    }

    this.employeService.ajouterSuivi(payload).subscribe({
      next: () => {
        alert('Suivi ajouté avec succès.');
        if (this.changerPosteVisible && this.suiviForm.nouveau_poste?.trim()) {
          const nv = this.suiviForm.nouveau_poste.trim();
          this.employeService.updateEmploye(this.selectedEmploye.id, { poste_actuel: nv }).subscribe({
            next: () => { this.selectedEmploye.poste_actuel = nv; this.initialPoste = nv; this.loadEmployes(); }
          });
        }
        this.addLocked.add(Number(this.selectedEmploye.id));
        this.persistLockset();
        this.saveProfilEmployeSiChange();
        this.selectEmploye(this.selectedEmploye);
      },
      error: () => alert('Erreur lors de l’ajout.')
    });
  }

  modifierSuivi() {
    if (!this.editingSuiviId) { alert('Aucun suivi sélectionné.'); return; }

    const notes: Record<string, number> = {};
    Object.keys(this.suiviForm.notes || {}).forEach((k) => {
      const v = this.suiviForm.notes[k];
      if (v != null) { const n = Number(v); if (!Number.isNaN(n)) notes[k] = n; }
    });

    const objectifs_plan = (this.suiviForm.objectifs_plan || [])
      .filter(r => (r.libelle || '').trim())
      .map(r => ({ libelle: r.libelle.trim(), delai: r.delai || null, evaluation_fin_cycle: (r.evaluation_fin_cycle || '').trim() }));

    const payload: any = {
      est_promotion: !!this.suiviForm.est_promotion,
      commentaire: (this.suiviForm.commentaire || '').trim(),
      notes,
      objectifs_plan
    };

    if (this.changerPosteVisible) {
      payload.ancien_poste = this.suiviForm.ancien_poste || null;
      payload.nouveau_poste = (this.suiviForm.nouveau_poste || '').trim();
    }

    this.employeService.updateSuivi(this.editingSuiviId, payload).subscribe({
      next: () => {
        alert('Suivi mis à jour avec succès.');
        if (this.changerPosteVisible && this.suiviForm.nouveau_poste?.trim()) {
          const nv = this.suiviForm.nouveau_poste.trim();
          this.employeService.updateEmploye(this.selectedEmploye.id, { poste_actuel: nv }).subscribe({
            next: () => { this.selectedEmploye.poste_actuel = nv; this.initialPoste = nv; this.loadEmployes(); }
          });
        }
        this.saveProfilEmployeSiChange();
        this.selectEmploye(this.selectedEmploye);
      },
      error: () => alert('Erreur lors de la mise à jour du suivi.')
    });
  }

  private saveProfilEmployeSiChange() {
    const patch: any = {};
    if ((this.selectedEmploye.departement || '') !== this.initialDept) patch.departement = this.selectedEmploye.departement || '';
    if ((this.selectedEmploye.poste_actuel || '') !== this.initialPoste) patch.poste_actuel = this.selectedEmploye.poste_actuel || '';
    if (Object.keys(patch).length === 0) return;
    this.employeService.updateEmploye(this.selectedEmploye.id, patch).subscribe({
      next: () => this.loadEmployes(),
      error: (e) => console.error('Maj employé échouée', e)
    });
  }
}
