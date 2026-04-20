import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';

import { EmployeService } from './employe.service';

describe('EmployeService', () => {
  let service: EmployeService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        EmployeService,
        provideHttpClient(),
        provideHttpClientTesting()
      ]
    });

    service = TestBed.inject(EmployeService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});