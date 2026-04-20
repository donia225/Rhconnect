import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';

import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { ToastrModule } from 'ngx-toastr';

import { EmployeListComponent } from './employe-list.component';

describe('EmployeListComponent', () => {
  let component: EmployeListComponent;
  let fixture: ComponentFixture<EmployeListComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [
        EmployeListComponent,
        NoopAnimationsModule,
        ToastrModule.forRoot()
      ],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting()
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(EmployeListComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});