논문용 최종 그림

주제마다 폴더 하나씩이고, 폴더 안에 학습곡선과 지표별 그림이 들어 있다.
모든 그림은 png와 pdf로 있다.

  Fig1_Communication        통신을 쓸 때와 쓰지 않을 때
  Fig2_MoE_Architecture     신경망 구조 네 가지
  Fig3_Message_Aggregation  메시지를 한 척에게 받을지 네 척에게 받을지
  Fig4_Message_Dimension    메시지 크기 2부터 12까지
  Fig5_COLREGs_Term         규정 준수 보상 항의 유무
  Fig6_Comm_Timing          통신을 처음부터 켤지 학습 중간부터 켤지
  Fig7_통통배               받기만 하는 배가 섞인 함대 (학습 아님, 평가만)
  Fig8_A_                   A* 전역경로 (학습 아님, 평가만)

Fig1~Fig6은 변수 하나씩만 바꿔 학습한 실험이고, Fig7과 Fig8은 학습을
다시 하지 않고 완성된 정책을 고정한 채 평가만 다르게 한 것이다.

폴더 안 파일 — Fig1 ~ Fig6

  0_reward_curve            학습이 진행되며 보상이 어떻게 변하는지
  1_colregs_compliance      규정 준수율 전체 평균
  2_colregs_by_situation    조우 상황별 규정 준수율
  3_collision_rate          충돌률
  4_fuel_consumption        연료 소비
  5_heading_travel          항해 중 뱃머리를 돌린 총량 (작을수록 부드러운 항로)
  6_min_separation          다른 배와 가장 가까웠던 거리
  7_episode_length          목적지 도달까지 걸린 시간

  Fig5에는 2_colregs_by_situation이 없다. 나머지 다섯 폴더에는 다 있다.
  주제를 설명한 description.txt는 Fig1~Fig5에만 있다.

폴더 안 파일 — Fig7

  번호 체계가 다르다. 학습곡선도 도착률 막대도 없고 지표 여섯 개뿐이다.

  1_colregs_compliance  2_min_separation  3_collision_rate
  4_fuel_consumption    5_heading_travel  6_episode_time

  RawData/ 안에 집계 전 자료가 같이 들어 있다.
  ※ RawData의 값은 이 폴더의 그림과 맞지 않는다. 시드 다섯 개(s42~s46)짜리
     다른 측정으로 보인다. 그림은 준수 51.4~52.3 · 충돌 1.08~2.60이고,
     RawData를 같은 방식으로 집계하면 준수 43.4~45.1 · 충돌 5.02~10.35다.
     논문에 자료를 붙일 때 어느 쪽이 최종인지 먼저 확인할 것.

폴더 안 파일 — Fig8

  아직 완성이 아니다. 한국-대만 항로 지도(Fig8_korea_taiwan)와 자리표시자
  (Fig8_지도&DT(예정))만 있고, 전역경로를 쓸 때와 안 쓸 때를 비교한 막대는
  아직 만들지 않았다. 평가 하네스와 검증은 끝나 있다.
  자세한 것은 Fig8_A_/code/EVAL_ASTAR_README.md.

측정 방법

성능 그림의 값은 학습이 끝난 뒤 정책을 고정하고 수천 번의 항해를 다시
돌려서 잰 것이다. 학습 중의 기록은 에피소드가 몰려서 끝나는 시점에 따라
흔들리기 때문에, 최종 성능 판단에는 쓰지 않았다.

조건마다 서로 다른 난수로 세 번씩 학습했고, 그림의 값은 그 평균이다.
막대 위의 세로선은 세 번 사이의 편차다. 규정 항을 뺀 조건과 분리형 구조만
한 번씩 학습해서 편차가 표시되지 않는다.

학습곡선의 세로 점선은 통신을 켠 시점이다. 그 이전은 모든 조건이 같은
상태이므로, 곡선이 갈라지는 지점이 통신이 작동하기 시작한 지점이다.
곡선의 세로축은 도착과 충돌, 시간 초과를 함께 반영한 값이며, 충돌에는
도착보다 큰 가중치를 두었다. 해상에서 충돌 비용이 지연 비용보다 훨씬
크기 때문이다. 가중치를 3배에서 15배까지 바꿔 봐도 결론은 같았다.

곡선은 15M까지만 그린다. 학습은 16.06M까지 돌렸다.

다시 만드는 방법

  스크립트는 저장소의 Python/plotting/ 안에 있다.

      python regenerate_all.py     곡선
      python build_final.py        Fig1~Fig6
      python make_mixed_fleet.py   Fig7   (build_final 다음에)

  순서를 지켜야 한다. build_final.py가 결과 폴더의 png/pdf를 전부 지우고
  다시 만들기 때문에, Fig7을 먼저 만들면 지워진다.
  Fig8은 이 파이프라인 밖이라 영향이 없다.

  ※ 스크립트가 읽는 자료 폴더 Python/plotting/_data 는 저장소에 없다.
     .gitignore가 로그와 csv를 빼고 있어서 커밋된 적이 없다. 원래 작업하던
     기계에만 있으므로, 그것 없이는 그림을 다시 만들 수 없다.

같이 보면 좋은 문서

  그림별 정리.md            그림마다 무엇을 비교했고 어떤 수치가 나왔는지
  그래프 매칭 정리.txt      어느 그림이 어느 실행에서 나왔는지
  알고리즘과 비교설계.md    무엇을 어떻게 학습·비교했는지
