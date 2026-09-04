(function(global){
  "use strict";
  const KNOWN=new Set([
    "dumbbells","barbell","ez_curl_bar","trap_bar","weight_plates","kettlebells","medicine_ball","bench","adjustable_bench","squat_rack","power_rack","preacher_bench","dip_station","pull_up_bar","cable_machine","lat_pulldown","seated_row_machine","chest_press_machine","shoulder_press_machine","leg_press_machine","leg_extension_machine","leg_curl_machine","pec_deck","calf_raise_machine","smith_machine","machine","rope_attachment","straight_bar_attachment","lat_bar_attachment","ankle_strap","bands","ab_wheel","foam_roller","yoga_mat","stability_ball","landmine_attachment","bodyweight","rings","suspension_trainer","treadmill","bike","rowing_machine","elliptical","stair_climber","jump_rope","sled","safety_squat_bar","swiss_bar","cambered_bar","axle_bar","fixed_barbells","sandbag","weighted_vest","clubs_maces","deadlift_platform","half_rack","wall_rack","glute_ham_developer","roman_chair","hyperextension_bench","decline_bench","hack_squat_machine","pendulum_squat","belt_squat_machine","v_squat_machine","hip_thrust_machine","hip_abductor_machine","hip_adductor_machine","standing_leg_curl","lying_leg_curl","seated_leg_curl","donkey_calf_machine","tibialis_machine","incline_press_machine","decline_press_machine","chest_supported_row_machine","high_row_machine","pullover_machine","lateral_raise_machine","rear_delt_machine","biceps_curl_machine","triceps_extension_machine","assisted_dip_pullup","v_bar_attachment","single_d_handle","triceps_v_bar","multi_grip_lat_bar","lifting_belt","lifting_straps","wrist_wraps","knee_sleeves","dip_belt","fractional_plates","barbell_collars","blocks","plyo_box","parallettes","pushup_handles","climbing_rope","monkey_bars","air_bike","spin_bike","recumbent_bike","ski_erg","arc_trainer","stepmill","curved_treadmill"
  ]);
  function icon(key){
    key=String(key||"").toLowerCase().replace(/[^a-z0-9_]/g,"");
    const asset=KNOWN.has(key)?key:"generic";
    return `<img class="equipment-image" src="assets/equipment/${asset}.svg" alt="" aria-hidden="true" loading="lazy" onerror="this.onerror=null;this.src='assets/equipment/generic.svg'">`;
  }
  global.ForgeEquipment=Object.freeze({icon,knownCount:KNOWN.size});
})(globalThis);
