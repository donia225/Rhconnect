import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { ActivatedRoute } from '@angular/router';
import { of } from 'rxjs';

import {EmployeLayoutComponent}  from './employe-layout.component';

describe('EmployeLayoutComponent', () => {
  let component: EmployeLayoutComponent;
  let fixture: ComponentFixture<EmployeLayoutComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [EmployeLayoutComponent],
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

    fixture = TestBed.createComponent(EmployeLayoutComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});