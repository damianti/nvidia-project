/**
 * Basic tests for billing service.
 */
import { billingService } from '@/services/billingService'

describe('BillingService', () => {
  it('should be defined', () => {
    expect(billingService).toBeDefined()
  })

  it('should have getAllBillingSummaries method', () => {
    expect(billingService.getAllBillingSummaries).toBeDefined()
    expect(typeof billingService.getAllBillingSummaries).toBe('function')
  })

  it('should have getBillingDetail method', () => {
    expect(billingService.getBillingDetail).toBeDefined()
    expect(typeof billingService.getBillingDetail).toBe('function')
  })
})

