# Preventive Maintenance Schedule - Q3 2025
## Batch Plant Production Equipment

**Document ID:** PM-SCHED-2025-Q1  
**Revision:** 3  
**Last Updated:** August 15, 2025  
**Next Review:** November 1, 2025

---

## Critical Maintenance Windows

### MIXER-01 (Primary Mixing Unit)
- **Next Scheduled PM:** August 16, 2025, 08:00-16:00
- **Type:** Quarterly Comprehensive
- **Duration:** 8 hours
- **Critical Components:**
  - Motor bearing replacement
  - Shaft alignment verification
  - Seal inspection and replacement
- **Production Impact:** FULL SHUTDOWN REQUIRED
- **Last PM Completed:** October 28, 2024
- **Overdue Status:** ON SCHEDULE

### REACTOR-01 (Batch Reactor)
- **Next Scheduled PM:** August 25, 2025, 06:00-18:00  
- **Type:** Semi-Annual Deep Clean
- **Duration:** 12 hours
- **Critical Components:**
  - Vessel interior inspection
  - Agitator blade measurement
  - Temperature probe calibration
  - Pressure relief valve testing
- **Production Impact:** FULL SHUTDOWN REQUIRED
- **Last PM Completed:** July 25, 2024
- **Overdue Status:** ON SCHEDULE

### FILLER-01 (Filling Machine)
- **Next Scheduled PM:** September 3, 2025, 10:00-14:00
- **Type:** Monthly Calibration
- **Duration:** 4 hours
- **Critical Components:**
  - Load cell calibration
  - Nozzle cleaning
  - Conveyor belt tension adjustment
- **Production Impact:** PARTIAL - Can operate at 50% capacity
- **Last PM Completed:** August 3, 2025
- **Overdue Status:** ON SCHEDULE

---

## Maintenance Rules and Constraints

### Production Scheduling Requirements
1. **Minimum Notice Period:** 72 hours for all production planning
2. **Buffer Time:** 2 hours required after maintenance before production can resume
3. **Validation Runs:** Product A requires 1 validation batch after reactor maintenance
4. **Concurrent Maintenance:** Mixer and Reactor cannot be maintained simultaneously

### Override Conditions
Maintenance can only be postponed if ALL conditions are met:
- Equipment health score > 85%  *(TOGGLE: Current score = 87%, change to 75% for NO-GO)*
- No critical alarms in last 7 days
- Written approval from Maintenance Manager
- Maximum postponement: 14 days

---

## Equipment Health Thresholds

| Equipment | Current Health Score | Minimum for Operation | Critical Threshold |
|-----------|---------------------|----------------------|-------------------|
| MIXER-01  | 91% | 70% | 60% |
| REACTOR-01| 87% | 75% | 65% |  *(TOGGLE: Change to 73% for NO-GO)*
| FILLER-01 | 94% | 70% | 60% |

---

## Special Considerations for Product Types

### Product A
- Cannot be produced within 24 hours after reactor maintenance
- Requires stable temperature control (±0.5°C) 
- Mixer speed variance must be <2% (check calibration date)

### Product B
- Can be produced immediately after maintenance
- Less sensitive to equipment variations
- Standard operating parameters apply

### Product C
- Requires specialized cleaning before and after (additional 4 hours)
- Cannot be scheduled within 48 hours of maintenance activities