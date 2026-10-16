# Phase 1-2 최종 Review

## 1. 목적

이 문서는 Phase 1-2의 B0~B7 전체 학습과 evidence chain을 최종적으로 연결하고,
Phase 1-2에서 실제로 입증한 것과 입증하지 못한 것을 구분하여 종료하기 위한
한국어 canonical closure artifact다.

이 문서는 새로운 구현 결과를 추가하지 않는다.

최종 review 기준은 다음과 같다.

```text
behavior preservation
object responsibility
encapsulation
Tell, Don't Ask
Rich Domain
SRP
DIP
test-first / safety net
AI evaluation pipeline
prompt constraint
change cost
overengineering
evidence-bounded interpretation
```

B0~B4의 개별 PASS는 앞선 MASTER 판정을 그대로 전제로 하며,
이번 최종 review에서는 그 학습이 B-5~B-7의 실제 코드와 실험 evidence에서
어떻게 이어졌는지를 중심으로 검수한다.

---

## 2. Final Repository 기준

최종 review 시작 기준:

```text
BRANCH=
refactor/b5-object-oriented-craft

FINAL_REVIEW_BASE_HEAD=
353c0b77159915279a4ec22e64c9378c164217ac
```

Execution 1에서 다음 repository guard가 확인됐다.

```ini
REPOSITORY_GUARD=PASS
B5_COMMIT_EXISTENCE=PASS
B5_CANONICAL_ANCESTRY=PASS
ARTIFACT_INVENTORY=PASS

WORKTREE=CLEAN
INDEX=CLEAN

MAIN_PRODUCTION_UNEXPECTED_MODIFICATION_AT_WORKTREE=NO
FROZEN_ARTIFACT_UNEXPECTED_MODIFICATION_AT_WORKTREE=NO
```

B-7 protocol frozen hash도 일치했다.

```text
a5-harness/b7/experiment-protocol.md

SHA256=
4248bbe3596267230d8542be4a8dd4c315c56034e05e7233d3692246c1613d97
```

---

## 3. B0~B7 Progression

Phase 1-2 progression은 다음과 같이 정리한다.

```ini
B0=PASS
B1=PASS
B2=PASS
B3=PASS
B4=PASS
B5=PASS
B6=PASS
B7=PASS
```

학습 progression은 단순히 원칙을 암기하는 순서가 아니라 다음 흐름으로 이어졌다.

```text
B0~B4
객체 책임 / 캡슐화 / Tell, Don't Ask / Rich Domain
SRP / DIP / behavior preservation / refactoring safety net
설계 변경과 의존성 변화 이해

→

B-5
Characterization Test로 기존 behavior 고정
실제 Manual Refactoring 수행
service에 있던 reservation 책임을 Ticket으로 이동
public mutation surface 축소

→

B-6
동일한 문제를 AI proposal 대상으로 전환
Gen / Critique / Independent Eval / Validate 계약 분리
Deterministic Final Decision으로 최종 authority 고정

→

B-7
Prompt constraint 차이를 통제된 A/B 조건으로 비교
initial minimality와 follow-up Point Payment change-cost를 함께 측정
overengineering과 future-proofing을 실제 변경 evidence로 재검토
```

---

## 4. B0~B4 학습과 B-5~B-7 Evidence 연결

### 4.1 객체 책임

객체 책임은 "어느 class에 method가 있는가"가 아니라
해당 상태와 규칙을 누가 소유해야 하는가의 문제로 학습했다.

B-5에서는 `TicketService`가 직접 처리하던 reservation state mutation과
reservation validation을 `Ticket`으로 이동했다.

따라서 객체 책임 학습은 실제 code shape 변화로 연결됐다.

### 4.2 캡슐화와 Tell, Don't Ask

B-5는 외부 service가 `Ticket`의 상태를 읽고 직접 setter를 호출하는 방향보다,
`Ticket`에게 예약 책임을 수행하도록 요청하는 방향으로 이동했다.

최종 B-5 단계에서는 reservation state 관련 public setter를 제거해
외부에서 invalid state transition을 만들 수 있는 mutation surface를 줄였다.

이 변화는 Tell, Don't Ask와 Rich Domain을 실제 diff로 연결한 evidence다.

### 4.3 SRP

`TicketService`는 orchestration을 담당하고,
`Ticket`은 자기 예약 가능 여부와 상태 전이를 담당하는 방향으로 책임을 분리했다.

이는 "class당 method 수를 줄인다"는 의미의 SRP가 아니라,
변경 이유와 도메인 책임을 더 일관된 위치에 두는 방향의 SRP로 해석한다.

### 4.4 DIP

Phase 1-2에서는 payment boundary가 `PaymentApi`라는 contract로 존재했고,
Point Payment는 이 boundary를 구현하는 방식으로 추가될 수 있었다.

따라서 상위 예약 흐름이 구체 결제 구현 자체에만 고정되지 않도록 하는
의존성 경계의 의미를 실제 변경에서 확인했다.

다만 Phase 1-2가 새로운 범용 payment architecture의 우월성을 입증한 것은 아니다.

### 4.5 Behavior Preservation

B-5의 핵심은 feature 추가보다 먼저 기존 behavior를 Characterization Test로 고정한 뒤
작은 refactoring step을 순서대로 수행한 것이다.

이 때문에 "설계가 더 좋아 보인다"는 판단과
"기존 behavior가 실제로 보존됐다"는 판단을 분리할 수 있었다.

---

## 5. B-5 Manual Refactoring Evidence

Canonical 범위:

```text
B5_START=
8cfcd6c1a6de43b6f2ce7a2acc031fee5ebed4f1

B5_END=
81140a1f681405ffbdedf946dd584b5b734e8e2d
```

Canonical commit chain:

```text
8cfcd6c1a6de43b6f2ce7a2acc031fee5ebed4f1
test: characterize original TicketService behavior

4039cbcb1f2cf673112051446e1cf80ae80ef32a
refactor: extract ticket reservation state change

05505aeed7f452b97387af5b5a65e061af11dfbc
refactor: move reservation state change to Ticket

9005e02eb0b1e0663676e16f537e7f6e6b35d0e4
refactor: move ticket reservation validation to Ticket

81140a1f681405ffbdedf946dd584b5b734e8e2d
refactor: encapsulate ticket reservation state
```

B5_START → B5_END에서 production change는 다음 두 파일에 집중됐다.

```text
src/main/java/com/gritmoments/objectcraft/Ticket.java
src/main/java/com/gritmoments/objectcraft/TicketService.java
```

최종적으로 확인한 핵심은 다음과 같다.

```text
TicketService 직접 reservation state mutation
→ Ticket responsibility

reservation validation
→ Ticket responsibility

public reservation-state setter
→ 제거

Characterization Test
→ safety net으로 보존
```

이 과정은 behavior-preserving refactoring과 feature change를 구분하게 했다.

B-5의 refactoring 목적은 새 payment feature를 추가하는 것이 아니라,
기존 reservation behavior를 보존하면서 책임과 캡슐화 구조를 개선하는 것이었다.

---

## 6. B-5 Point Payment Learning

B-5 이후 Point Payment reference implementation commit은 다음이다.

```text
c3661c17f30e2434...
feat: add point payment
```

추가된 핵심 production/test surface는 다음과 같다.

```text
PointBalanceRepository
PointPayment
PointPaymentTest
```

`PointPayment`는 `PaymentApi`를 구현하고,
balance가 충분하면 deduct 후 success,
부족하면 deduct하지 않고 failure를 반환하는 behavior를 가진다.

이 단계에서 학습한 질문은 다음이다.

```text
새 requirement가 들어왔을 때
기존 설계가 실제로 어떤 변경비용을 만드는가?
```

단 다음 causal limitation은 유지한다.

```text
original baseline에 동일 Point Payment requirement를
별도로 구현한 direct A/B 없음
```

따라서 B-5 Point Payment reference 하나만으로
B-5 refactoring이 Point Payment change cost를 인과적으로 감소시켰다고
강하게 주장하지 않는다.

---

## 7. Test-First / Safety-Net Learning

### 7.1 Characterization Test가 먼저 필요한 이유

refactoring은 외부 behavior를 바꾸지 않고 내부 구조를 바꾸는 작업이다.

따라서 기존 behavior를 먼저 고정하지 않으면,
구조 변경 중 발생한 regression과 의도된 변화의 경계를 증명하기 어렵다.

B-5에서는 Characterization Test를 refactoring 시작점에 먼저 두었다.

### 7.2 Behavior Preservation 증명

B-5에서는 다음 순서로 변경했다.

```text
Characterization Test
→ Extract
→ responsibility movement
→ validation movement
→ encapsulation
```

작은 단계마다 기존 behavior safety net을 유지하는 방식으로
구조 변경과 behavior 변경을 분리했다.

### 7.3 Regression Test와 Feature Test의 차이

Characterization / regression test는
이미 존재하는 reservation behavior가 깨지지 않았음을 확인한다.

새 Point Payment test는
새 requirement 자체의 behavior가 맞는지 확인한다.

따라서 두 test는 역할이 다르다.

```text
Regression / Characterization
= 기존 behavior 보호

Feature Test
= 새 requirement 검증
```

---

## 8. B-6 AI Refactoring Pipeline

B-6에서는 다음 pipeline contract를 구현하고 실제 canonical run을 수행했다.

```text
Canonical Fixture
→ Gen
→ Critique
→ Independent Eval
→ Validate
→ Deterministic Final Decision
```

Canonical AI Run:

```text
RUN_ID=
b6-canonical-postauth-20261016T102757Z

EXECUTION_STATUS=
COMPLETE

FINAL_DECISION=
REJECT
```

B-6에서 중요한 학습은 AI output을 바로 정답으로 채택하지 않았다는 점이다.

### 8.1 Manual Solution Leakage Guard

Frozen canonical fixture를 사용하고
B-5 manual solution 자체를 정답으로 노출하지 않은 상태에서
AI proposal을 생성했다.

### 8.2 Role Independence

Gen, Critique, Independent Eval, Validate를
서로 다른 역할과 contract로 분리했다.

Eval score 하나가 전체 pipeline의 최종 verdict가 되지 않도록 했다.

### 8.3 Schema Contract

AI output은 의미적으로 좋아 보이는 것만으로 충분하지 않았다.

실제 Critique에서는 substantive semantic issue가 존재했고,
동시에 required schema field 누락으로 contract compliance가 실패했다.

### 8.4 Evidence Sufficiency

Evidence Sufficiency를 별도 gate로 유지했다.

평가자가 높은 점수를 주었더라도
필요한 evidence가 없는 claim을 최종 acceptance 근거로 사용할 수 없도록 했다.

### 8.5 Hard Gates와 Final Authority

Canonical runtime evidence는 다음과 같다.

```text
EVAL_TOTAL=17
EVIDENCE_SUFFICIENCY=SUFFICIENT
VALIDATION_STATUS=FAIL
CRITIQUE_BLOCKERS=3

FINAL_DECISION=REJECT
```

높은 Eval score가 Critique blocker와 hard-gate failure를 override하지 못했다.

최종 authority는 AI self-verdict가 아니라 deterministic decision rule에 있었다.

---

## 9. B-6 PASS의 의미

다음 두 문장을 동일시하지 않는다.

```text
B6=PASS
```

```text
AI proposal=PASS
```

B-6 PASS의 의미는 다음이다.

```text
Canonical Fixture / Gen / Critique / Independent Eval / Validate /
Deterministic Final Decision을 실제로 구현하고 실행했으며,

그 결과가 REJECT여도 결과 개선을 위한 tuning이나 rerun으로 덮지 않고
canonical evidence로 보존했다.
```

즉 B-6은 성공한 AI 답안을 만드는 실험이 아니라,
AI refactoring output을 evidence와 deterministic gate로 평가하는
실험 pipeline을 완결한 단계다.

---

## 10. B-5 Manual vs B-6 AI Evidence Level

B-5 Manual evidence:

```text
ACTUAL CODE
ACTUAL DIFF
ACTUAL CHARACTERIZATION / BEHAVIOR EVIDENCE
```

B-6 AI evidence:

```text
ACTUAL AI PROPOSAL
ACTUAL CRITIQUE
ACTUAL INDEPENDENT EVAL
ACTUAL VALIDATE
ACTUAL DETERMINISTIC FINAL DECISION
```

하지만 B-6에서는 AI-generated production patch를 materialize하지 않았다.

따라서 다음을 유지한다.

```ini
AI_CODE_MATERIALIZED=NO
AI_ACTUAL_DIFF_AVAILABLE=NO
AI_ACTUAL_BUILD_EVIDENCE=NO
AI_ACTUAL_CHARACTERIZATION_EVIDENCE=NO

DIRECT_MANUAL_VS_AI_CODE_COST_COMPARISON=NO
```

이 차이를 제거하거나
Manual과 AI implementation cost를 직접 비교한 것처럼 해석하지 않는다.

---

## 11. B-7 Prompt A/B Experiment

Canonical artifacts:

```text
a5-harness/b7/experiment-protocol.md
a5-harness/b7/initial-ab-comparison.md
a5-harness/b7/point-payment-change-cost.md
a5-harness/b7/final-prompt-comparison.md
```

B-7은 동일 frozen baseline에서
Prompt constraint 차이가 실제 code shape과 change surface에
어떤 영향을 만드는지 비교했다.

### Prompt A

```text
낮은 design constraint
설계 결정의 더 많은 부분을 AI에 위임
```

### Prompt B

```text
명시적 Problem Definition / Design Constraints
evidence 기반
최소 변경
future-only abstraction 금지
public contract 최소화
```

Point Payment requirement는 initial refactoring input에서 제외하고,
initial result가 동결된 뒤 동일한 frozen follow-up requirement로 제공했다.

---

## 12. Initial Refactoring Learning

Initial canonical executions에서는 Prompt B가 더 constrained하고 minimal했다.

관찰된 방향:

```text
Prompt B
→ fewer new methods
→ smaller new public surface
→ smaller diff surface
→ state-transition encapsulation에 더 가까운 scope
```

Prompt A는 Ticket 책임 이동 외에도
service orchestration을 더 넓게 decomposition했다.

따라서 다음은 evidence로 유지할 수 있다.

```text
이 두 canonical executions에서는
명시적 Problem Definition과 Design Constraints가
actual code structure와 initial change scope에 영향을 주었다.
```

하지만 이 결과만으로
Prompt B가 일반적으로 항상 더 좋은 prompt라고 주장하지 않는다.

---

## 13. Point Payment Change-Cost Learning

동일한 frozen Point Payment requirement를
Prompt A initial result와 Prompt B initial result에 각각 적용했다.

이 두 canonical executions에서는:

```text
Initial refactoring
→ Prompt B가 더 minimal

Point Payment follow-up
→ Prompt A-derived design이 더 작은 추가 change surface
```

Prompt A initial의 일부 service/domain decomposition은
Point Payment 단계에서 실제로 재사용됐다.

Prompt B의 `Ticket.reserve(...)` domain abstraction도 재사용됐지만,
service orchestration에서는 추가 decomposition이 필요했다.

따라서 다음을 학습했다.

```text
smallest initial diff
!=
lowest observed follow-up change cost
```

이는 "처음부터 크게 만들자"는 결론도 아니고,
"항상 최소 변경이 정답이다"라는 결론도 아니다.

---

## 14. Minimality Learning

다음 두 개념을 구분한다.

```text
smallest possible current diff

vs

smallest justified design change
```

현재 requirement로 설명되지 않는 future-only structure를 미리 추가하는 것은 피한다.

반대로 현재 책임 분리와 실제 code pressure로 정당화되는 구조까지
단순히 diff가 더 크다는 이유로 제거하는 것도 정답으로 취급하지 않는다.

설계 판단은 현재 requirement와 실제 변경 evidence를 함께 본다.

---

## 15. Overengineering Learning

Phase 1-2에서는 overengineering을 다음만으로 판정하지 않는다.

```text
class 개수
interface 개수
pattern 이름
```

최종 판단 기준은 다음이다.

```text
현재 requirement
실제 code pressure
추가 abstraction
실제 사용 여부
후속 변경에서의 benefit / cost
public surface
change surface
```

B-7에서 Prompt A initial은 minimum보다 넓은 decomposition을 보였지만,
일부 구조가 Point Payment follow-up에서 실제로 재사용됐다.

Prompt B도 architecture-level abstraction explosion은 없었지만,
follow-up에서 frozen requirement가 필수로 요구하지 않은
추가 public exception surface가 관찰됐다.

따라서 broader decomposition을 자동으로 overengineering이라고 보거나,
작은 initial diff를 자동으로 적정설계라고 보지 않는다.

---

## 16. AI 활용 최종 Learning

Phase 1-2에서 AI는 최종 설계 authority가 아니었다.

AI의 역할은 다음에 가까웠다.

```text
proposal generator
+
critic / evaluator input
```

최종 authority는 다음 evidence와 rule에 두었다.

```text
frozen requirement
actual code evidence
tests / build
schema contract
Evidence Sufficiency
hard gates
deterministic final decision
human experiment interpretation
```

이 구조는 Eval score가 높아도
contract와 evidence가 부족하면 최종 acceptance를 막을 수 있게 했다.

---

## 17. Phase 1-2가 Demonstrated 한 것

Phase 1-2는 다음을 실제 learning/evidence chain으로 보여줬다.

1. 기존 code behavior를 먼저 Characterization Test로 고정하고 refactoring을 시작할 수 있다.
2. service에 몰린 reservation responsibility를 domain object로 이동할 수 있다.
3. encapsulation으로 외부 public mutation surface를 줄일 수 있다.
4. Tell, Don't Ask / Rich Domain / SRP를 실제 refactoring diff와 책임 이동으로 설명할 수 있다.
5. `PaymentApi` boundary를 통해 구체 payment implementation과 상위 흐름의 의존성 경계를 설명할 수 있다.
6. behavior-preserving refactoring과 새 feature change를 구분할 수 있다.
7. AI refactoring output을 Gen / Critique / Independent Eval / Validate / Deterministic Final Decision pipeline으로 평가할 수 있다.
8. 높은 AI Eval score와 final authority를 분리할 수 있다.
9. Prompt constraint가 actual AI code structure와 initial change scope에 영향을 줄 수 있음을 관찰했다.
10. initial minimality와 follow-up change-cost 사이 trade-off를 실제 code/change evidence로 분석했다.
11. overengineering을 단순 abstraction count가 아니라 requirement와 actual reuse/change evidence로 판단할 수 있다.
12. evidence보다 강한 causal/generalized claim을 피하고 limitation을 보존할 수 있다.

---

## 18. Phase 1-2가 Demonstrated 하지 못한 것

Phase 1-2는 다음을 입증하지 못했다.

```text
특정 Prompt 스타일의 통계적 우월성

Prompt B가 일반적으로 항상 Prompt A보다 우수함

Prompt A가 일반적으로 future change에 더 강함

모든 backend domain에 동일 결과가 일반화됨

모든 future requirement에서 동일한 change-cost pattern이 재현됨

AI가 manual보다 일반적으로 우수하거나 열등함

특정 abstraction/decomposition 방식의 보편적 우월성

single canonical run의 stochasticity 제거

model/provider output variability 제거

original baseline과 refactored baseline에
동일 Point Payment requirement를 구현한 direct causal A/B

B-5 Manual과 B-6 AI materialized production patch의
직접 code/build/regression/change-cost 비교
```

---

## 19. Limitations

B-7 실험 자체의 핵심 한계:

```text
각 condition canonical execution 1회

모델 stochasticity 존재

Prompt A/B 실행 순서 완전 randomization 없음

하나의 작은 Ticket reservation domain만 사용

하나의 follow-up Point Payment requirement만 사용

provider/model을 동일하게 고정했어도
output variability를 완전히 제거하지 못함
```

B-5 Point Payment causal limitation:

```text
original baseline direct implementation과
B-5-refactored baseline direct implementation의
동일 requirement A/B가 없음
```

B-6 evidence-level limitation:

```text
AI production patch를 materialize하지 않음
```

따라서 최종 결론은
Phase 1-2의 실제 canonical executions와 repository evidence 범위 안에서만 해석한다.

---

## 20. Evidence Chain

### B-5

```text
8cfcd6c Characterization Test
→
4039cbc Extract
→
05505ae responsibility movement
→
9005e02 validation movement
→
81140a1 encapsulation
→
c3661c1 Point Payment reference implementation
```

### B-6

```text
73c7baa Canonical Fixture
→
f794add Gen contract
→
52e8267 Critique contract
→
eb52731 Eval contract
→
e6b2050 Validate / deterministic gates
→
339ab8e live runner
→
2e0b786 manual-vs-ai comparison
```

Canonical AI result:

```text
b6-canonical-postauth-20261016T102757Z
→ COMPLETE
→ FINAL_DECISION=REJECT
```

### B-7

```text
4e54529 experiment protocol
→
06453ef initial Prompt A/B comparison
→
f0a718b Point Payment change-cost comparison
→
353c0b7 final Prompt comparison
```

Required artifact inventory:

```text
a5-harness/b6/manual-vs-ai-comparison.md

a5-harness/b7/experiment-protocol.md
a5-harness/b7/initial-ab-comparison.md
a5-harness/b7/point-payment-change-cost.md
a5-harness/b7/final-prompt-comparison.md
```

Execution 1에서 모두 존재하며 frozen artifact의 unexpected worktree modification이 없음을 확인했다.

---

## 21. 최종 자기평가

Phase 1-2의 핵심 성과는
OOP/SOLID 용어를 설명하는 수준에서 끝나지 않고,
작은 Ticket reservation domain에서 실제 refactoring sequence,
Characterization Test, AI evaluation pipeline, controlled prompt comparison,
follow-up change-cost evidence까지 연결했다는 점이다.

현재 도달 수준은 다음처럼 평가한다.

```text
객체 책임 / 캡슐화
→ 실제 code refactoring으로 설명 가능

Tell, Don't Ask / Rich Domain / SRP
→ Ticket reservation 책임 이동과 public setter 제거로 설명 가능

DIP
→ PaymentApi boundary와 alternate payment implementation 관점에서 설명 가능

Behavior Preservation / Test-First
→ Characterization Test 선행과 단계적 refactoring으로 설명 가능

AI 활용
→ proposal 생성과 final authority를 분리해 설명 가능

Prompt Engineering
→ 문구 취향이 아니라 actual code scope/change evidence로 비교 가능

Overengineering
→ abstraction count가 아니라 requirement / reuse / change-cost evidence로 판단 가능

실험 해석
→ observed result와 generalized causal claim을 구분 가능
```

동시에 Phase 1-2는 작은 domain과 적은 canonical run에 기반한다.

따라서 "원칙을 이해했다"는 것과
"다양한 production-scale system에서도 동일한 판단을 반복해서 할 수 있다"는 것은
아직 같은 수준으로 취급하지 않는다.

---

## 22. Next Phase Entry Recommendation

다음 phase에서는 Phase 1-2에서 만든 판단 기준을 더 넓은 문제에 적용하는 것이 적절하다.

우선순위는 다음과 같다.

```text
1. 더 큰 orchestration / domain boundary에서
   responsibility와 dependency decision 반복

2. Characterization / regression / feature test 역할을
   더 복잡한 state transition에서 유지

3. AI proposal을 실제 materialized patch까지 연결하되
   build / test / diff / behavior evidence를 함께 수집

4. single-run Prompt 비교가 아니라
   반복 execution 또는 더 다양한 requirement로
   stochasticity와 generalization 한계 축소

5. abstraction 도입 여부를
   current pressure + actual reuse + future change evidence로 계속 검증
```

즉 다음 phase의 목표는 새 pattern을 많이 배우는 것이 아니라,
Phase 1-2에서 만든 evidence-based design judgment를
더 큰 scope에서 반복 가능하게 만드는 것이다.

---

## 23. Final Review 판정 기준

이 artifact 설치 자체로 Phase 1-2를 즉시 CLOSED 처리하지 않는다.

최종 commit 이후 다음을 다시 확인해야 한다.

```text
B0~B7 모두 PASS

evidence chain 연결 가능

unexpected production modification 없음

frozen artifact unexpected modification 없음

final closure artifact 외 예상하지 않은 변경 없음

worktree clean

final HEAD 확인

PUSH=NO
MERGE=NO
```

위 조건을 모두 만족하는 최종 guard 이후에만:

```ini
PHASE_1_2=PASS
PHASE_1_2_STATUS=CLOSED
```

를 확정한다.
