## 2026-10-02T15:46:17Z
You are assigned to implement Phase 10 (Email - Admin Only) of the Project/Thesis Management System (PTMS) frontend.
Your working directory is: c:\Users\USERAS\Desktop\Defense Frontend\defense-frontend\.agents\teamwork\swe_phase10_1
The project root is: c:\Users\USERAS\Desktop\Defense Frontend\defense-frontend
The verbatim user request is recorded in: c:\Users\USERAS\Desktop\Defense Frontend\defense-frontend\ORIGINAL_REQUEST.md (and .agents/teamwork/ORIGINAL_REQUEST.md).

Please review ORIGINAL_REQUEST.md, docs/PROJECT_SPEC.md, docs/PHASES.md, and docs/api/openapi.yaml.

Requirements:
### R1. Email Service and API Types
Implement `src/types/email.ts` representing the five email request/response payloads (`BoardAssignmentsEmailRequest`, `DefenseDatesEmailRequest`, etc.) according to `docs/api/openapi.yaml`. Implement `src/features/email/api/email.service.ts` connecting to the 5 email endpoints using `apiClient`. Implement React Query mutations in `use-email.ts` for these 5 actions.

### R2. Admin Email Tab UI
Create an `AdminEmailTab` component in `src/features/email/admin/components/admin-email-tab.tsx` that exposes UI controls (e.g. buttons/cards) to trigger the 5 email endpoints. Allow the admin to optionally provide filters (e.g., `boardType`, `defenseType`, `facultyId`) before sending, or just provide simple Send buttons that confirm the action. Use the project's existing `useToast` to report successes and errors. 

### R3. Tab Integration
Inject the `AdminEmailTab` into the `AdminBatchDetailsPage` component (`src/features/batches/admin/admin-batch-details-page.tsx`) as the "Emails" tab. Update the phase status in `docs/PHASES.md` from "Not started" to "Completed".

Acceptance Criteria:
- All request payloads match `openapi.yaml`.
- API calls are prefixed with `/v1/batches/{batchId}/email/`.
- The `AdminEmailTab` renders correctly within the batch details page.
- 5 distinct actions are available (Board Assignments, Mid Dates, Final Dates, Supervisor Feedback, Absent List).
- Type checks (`npx tsc --noEmit` with `$env:CI="true";` prefix on powershell) pass without errors for the new feature.

Ensure you maintain `progress.md` and `BRIEFING.md` in your working directory c:\Users\USERAS\Desktop\Defense Frontend\defense-frontend\.agents\teamwork\swe_phase10_1.
When finished and all acceptance criteria are met, report victory back to parent with your handoff summary.
