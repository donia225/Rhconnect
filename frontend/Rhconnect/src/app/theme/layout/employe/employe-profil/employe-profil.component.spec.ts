import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { ActivatedRoute } from '@angular/router';
import { of } from 'rxjs';

import {EmployeProfilComponent}  from './employe-profil.component';

describe('EmployeProfilComponent', () => {
  let component: EmployeProfilComponent;
  let fixture: ComponentFixture<EmployeProfilComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [EmployeProfilComponent],
      providers: [
  provideHttpClient(),
  provideHttpClientTesting(),
  {
    provide: ActivatedRoute,
    useValue: {
      snapshot: { paramMap: { get: () => null } },
      params: of({}),
      queryParams: of({})
    }
  }
]
    }).compileComponents();

    fixture = TestBed.createComponent(EmployeProfilComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});