import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { EmployeService } from 'src/app/services/employe/employe.service';

type Suivi = {
  ancien_poste?: string | null;
  nouveau_poste: string;
  date_changement?: string | null;
  est_promotion: boolean;
  commentaire?: string | null;
  notes?: Record<string, number>;
  objectifs_plan?: Array<{ libelle: string; delai?: string | null; evaluation_fin_cycle?: string | null }>;
};

@Component({
  selector: 'app-mon-suivi',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './mon-suivi.component.html',
  styleUrls: ['./mon-suivi.component.scss']
})
export class MonSuiviComponent implements OnInit {
  loading = true;
  profil: any = null;
  suivis: Suivi[] = [];

  constructor(private employeService: EmployeService) {}

  ngOnInit(): void {
    this.employeService.getMonProfilEtSuivi().subscribe({
      next: (data: any) => {
        this.profil = data?.profil ?? null;
        this.suivis = (data?.suivi_carriere ?? [])
          .slice()
          .sort((a: any, b: any) =>
            new Date(b?.date_changement || 0).getTime() - new Date(a?.date_changement || 0).getTime()
          );
        this.loading = false;
      },
      error: () => (this.loading = false)
    });
  }

  fmtDate(d?: string | null) {
    if (!d) return '—';
    const t = new Date(d);
    if (isNaN(t.getTime())) return d;
    return t.toLocaleDateString(undefined, { day: '2-digit', month: 'long', year: 'numeric' });
  }
}
