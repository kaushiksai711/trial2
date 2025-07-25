; Medical domain knowledge base

; Medical conditions
(is_a diabetes medical_condition)
(is_a type_2_diabetes diabetes)
(is_a type_1_diabetes diabetes)

; Treatments
(treats insulin diabetes)
(treats metformin type_2_diabetes)
(treats diet_control diabetes)

; Symptoms
(symptom_of increased_thirst diabetes)
(symptom_of frequent_urination diabetes)
(symptom_of fatigue diabetes)

; Risk factors
(risk_factor obesity type_2_diabetes)
(risk_factor family_history diabetes)
(risk_factor age type_2_diabetes)

; Complications
(complication_of kidney_disease diabetes)
(complication_of heart_disease diabetes)
(complication_of nerve_damage diabetes)

; Prevention methods
(prevents healthy_diet type_2_diabetes)
(prevents regular_exercise type_2_diabetes)
(prevents weight_management diabetes)

; Relationships and hierarchies
(is_a "chronic_disease" "medical_condition")
(is_a "diabetes" "chronic_disease")

; Required for management
(required_for "glucose_monitoring" "diabetes_management")
(required_for "regular_exercise" "diabetes_management") 