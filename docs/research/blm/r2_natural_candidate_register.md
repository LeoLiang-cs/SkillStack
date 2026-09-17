# R2 自然候选登记

本登记只记录零模型 Producer/adapter 预筛选；不把历史 run 当作 R2 live outcome，也不产生 R3 verdict。

- boundary：`r2_c2_structured_react_first_handoff`
- evidence class：`not_verified`
- eligible cases：`0`

## r2_trial_T20190907_051013_060265

- task：`valid_unseen/pick_two_obj_and_place-CD-None-Safe-308/trial_T20190907_051013_060265`
- instruction：Transfer the two CDs from the desk to the vault.
- environment runtime：`{'available': False, 'error': "ModuleNotFoundError: No module named 'alfworld'"}`
- carrier difference：`True`
- eligible：`False`
- gate reasons：`['initial_reset_not_reconstructable', 'alfworld_runtime_unavailable']`
- TaskSemantic label assistance：`task_family` only; `expected_skill_id` read = `False`; deployment-unassisted = `False`

- lexical: ['skill_light_inspection', 'skill_pick_two_then_place'] / input `fc0a336c06e75f1e20418269a135377ffe94140d8b6a8ee62b17e94462b4fbf9`
- task_semantic: ['skill_pick_two_then_place', 'skill_clean_then_place'] / input `8f1c4457034cfcc25382227181504ad2394aa4506fc7d5ffb85194fb10dfcbf7`

## r2_trial_T20190908_010306_215435

- task：`valid_unseen/pick_two_obj_and_place-PepperShaker-None-Drawer-10/trial_T20190908_010306_215435`
- instruction：Put two shakers in a drawer.
- environment runtime：`{'available': False, 'error': "ModuleNotFoundError: No module named 'alfworld'"}`
- carrier difference：`False`
- eligible：`False`
- gate reasons：`['no_consumer_read_domain_carrier_difference', 'initial_reset_not_reconstructable', 'alfworld_runtime_unavailable']`
- TaskSemantic label assistance：`task_family` only; `expected_skill_id` read = `False`; deployment-unassisted = `False`

- lexical: ['skill_pick_two_then_place', 'skill_clean_then_place'] / input `583dda36e1896a6dc1e47559d8252a089d80de77a1550b0c3c53b6446e0e6b53`
- task_semantic: ['skill_pick_two_then_place', 'skill_clean_then_place'] / input `8f1c4457034cfcc25382227181504ad2394aa4506fc7d5ffb85194fb10dfcbf7`

## r2_trial_T20190907_163240_345855

- task：`valid_unseen/pick_two_obj_and_place-Pillow-None-Sofa-219/trial_T20190907_163240_345855`
- instruction：Put two pillows on the sofa.
- environment runtime：`{'available': False, 'error': "ModuleNotFoundError: No module named 'alfworld'"}`
- carrier difference：`False`
- eligible：`False`
- gate reasons：`['no_consumer_read_domain_carrier_difference', 'initial_reset_not_reconstructable', 'alfworld_runtime_unavailable']`
- TaskSemantic label assistance：`task_family` only; `expected_skill_id` read = `False`; deployment-unassisted = `False`

- lexical: ['skill_pick_two_then_place', 'skill_clean_then_place'] / input `583dda36e1896a6dc1e47559d8252a089d80de77a1550b0c3c53b6446e0e6b53`
- task_semantic: ['skill_pick_two_then_place', 'skill_clean_then_place'] / input `8f1c4457034cfcc25382227181504ad2394aa4506fc7d5ffb85194fb10dfcbf7`

## Claim boundary

`historical_evidence` 仅用于冻结候选集合；若首次 reset 不能重建，候选保持 `not_verified`，不得进入 live arm。自然发现必须交给独立 R3 confirmation。
