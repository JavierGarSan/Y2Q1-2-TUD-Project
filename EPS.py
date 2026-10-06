import math
# ONE ORBIT CALCULATION
power_values = { # Watts
    "Payload": 543.2,  
    "Pléiades-HiRi": 400.0,
    "PROBA-VGT-3": 43.2,
    "Sentinel-3_SLSTR": 100.0,
    "Propulsion": 0.0,
    "Attitude_Control": 79.0,
    "Communications": 69.1,
    "C&DH": 59.3,
    "Thermal_Control": 39.5,
    "Electric_Power": 197.5,
    "Structure": 0.0,
}

path_efficiency ={ #scalar
    "day": 0.8,
    "eclipse": 0.6,
}

durations={ #seconds
    "day":65.9*60,
    "eclipse":34.4*60,
    "max_communication":12.5*60,
}

# Apply once to sizing loads; derived powers, capacities, masses, areas and
# volumes inherit the margin. Physical properties and efficiencies stay fixed.
safety_margin=1.5

# Reader pp. 119-120, Eq. 68: distinguish load energy from array-side energy.
eclipse_load_energy=0
def energyusedinoneorbit():
    energy_total=0

    #day, All payload, ADCS, C&DH, Thermal control, EPS active. Communications added in case all communication takes place all over the day.
    day_energy=safety_margin*((durations["day"]*(power_values["Payload"]+power_values["Attitude_Control"]+power_values["C&DH"]+power_values["Thermal_Control"]+power_values["Electric_Power"]) + durations["max_communication"]*power_values["Communications"])/path_efficiency["day"])
    energy_total+=day_energy
    #eclipse.  Sentinel-3_SLSTR , ADCS,C&DH, Thermal control,  EPS active. Communications added in case all communication takes place over the eclipse.
    global eclipse_load_energy, eclipse_energy
    eclipse_load_energy=safety_margin*((durations["eclipse"]*(power_values["Sentinel-3_SLSTR"]+power_values["Attitude_Control"]+power_values["C&DH"]+power_values["Thermal_Control"]+power_values["Electric_Power"])) + durations["max_communication"]*power_values["Communications"])
    eclipse_energy=eclipse_load_energy/path_efficiency["eclipse"]

    energy_total+=eclipse_energy

    print(day_energy)
    print(eclipse_energy)
    print(energy_total)

    return energy_total # E

peakPower=1185.2 #W
energy_one_orbit=energyusedinoneorbit()



# SOLAR ARRAY SIZING
solar_panels = {
    "HES_rigid": {"W_per_kg": 58.5, "eff": 0.19, "cost_min_K_per_W": 0.5, "cost_max_K_per_W": 1.5, "deg_per_yr": 0.04},
    "HES_flex": {"W_per_kg": 114.0, "eff": 0.19, "cost_min_K_per_W": 1.0, "cost_max_K_per_W": 2.0, "deg_per_yr": 0.04},
    "TJ_GaAs_rigid": {"W_per_kg": 70.0, "eff": 0.268, "cost_min_K_per_W": 0.5, "cost_max_K_per_W": 1.5, "deg_per_yr": 0.005},
    "TJ_GaAs_ultraflex": {"W_per_kg": 115.0, "eff": 0.268, "cost_min_K_per_W": 1.0, "cost_max_K_per_W": 2.0, "deg_per_yr": 0.005},
    # CIGS degradation is a 0.5%/yr estimate for Ascent Solar's space-oriented Titan module,
    # not a measured rate for this panel: https://www.sec.gov/Archives/edgar/data/1350102/000107997324000261/asti_s1.htm
    "CIGS_film": {"W_per_kg": 275.0, "eff": 0.11, "cost_min_K_per_W": 0.1, "cost_max_K_per_W": 0.3, "deg_per_yr": 0.005},
    "aSi_MJ_film": {"W_per_kg": 353.0, "eff": 0.14, "cost_min_K_per_W": 0.05, "cost_max_K_per_W": 0.3, "deg_per_yr": 0.04},
    # Units: W_per_kg = W/kg; eff = scalar; cost_min/max_K_per_W = $1,000/W; deg_per_yr = scalar.
}
# Reader p. 123, Table 41: array area per BOL kW at 1 AU, normal incidence.
# These array-level values already account for the array construction.
array_area_per_kW = {
    "HES_rigid": 4.45,
    "HES_flex": 5.12,
    "TJ_GaAs_rigid": 3.12,
    "TJ_GaAs_ultraflex": 3.62,
    "CIGS_film": 7.37,
    "aSi_MJ_film": 5.73,
}
for name,panel in solar_panels.items():
    panel["area_m2_per_kW"] = array_area_per_kW[name]
# Table 41 marks both thin-film entries as projected performance.
solar_incidence_angle_deg=0.0 # Assumes Sun-pointing arrays; Eq. 78.
distance_to_sun_AU=1.0 # Eqs. 79-80.
lengthofmission=5 #years

print("#########################")
print("# Solar panel & Battery #")
print("#########################")


def solararraypowerreq(solar_panel):
    return (energy_one_orbit/durations["day"])/((1-(solar_panel["deg_per_yr"]))**lengthofmission)


def massSolarArray(solar_panel):
    effective_specific_power=solar_panel["W_per_kg"]*math.cos(math.radians(solar_incidence_angle_deg))/distance_to_sun_AU**2
    return solararraypowerreq(solar_panel)/effective_specific_power

def areaSolarAray(solar_panel):
    power_density=(1000/solar_panel["area_m2_per_kW"])*math.cos(math.radians(solar_incidence_angle_deg))/distance_to_sun_AU**2
    return solararraypowerreq(solar_panel)/power_density #m^2; Eq. 74


#for name,panel in solar_panels.items():
#    print(f"{name}: \n  PowerReq: {solararraypowerreq(panel)} Mass: {massSolarArray(panel)}, Area {areaSolarAray(panel)} ")

# Battery sizing
specific_energy = 90 #Wh/kg Table 43.
vol_energy_density=250 #Wh/L Table 43.
battery_to_load_efficiency=0.8 # Assumed discharge/transfer efficiency, Eqs. 81-82.
JtoWh=1/3600
depth_of_discharge=0.53 # Assumption: for ~26,200 LEO cycles.

def energy_battery():
    # Eq. 81 uses load energy, not array-side recharge energy (Eq. 68).
    return eclipse_load_energy*JtoWh/(battery_to_load_efficiency*depth_of_discharge) #Wh

def battery_weight():
    return energy_battery()/specific_energy #kg, battery only; Eq. 83

def battery_volume():
    return energy_battery()/vol_energy_density #L; Eq. 84

print(f"Battery capacity (Wh): {energy_battery()}") #Wh
print(f"Battery weight (kg): {battery_weight()}") #Kg
print(f"Battery volume (L): {battery_volume()}")

# Reader pp. 122-126, Eqs. 72 and 85: PMD is 30.3% of TOTAL EPS mass.
pmd_mass_fraction=0.303

def total_eps_mass(solar_panel):
    return (massSolarArray(solar_panel)+battery_weight())/(1-pmd_mass_fraction)

def pmd_mass(solar_panel):
    return pmd_mass_fraction*total_eps_mass(solar_panel)

print(f"EPS totals using the 30.3% PMD fraction (includes {safety_margin:g}x sizing margin):")
for name,panel in solar_panels.items():
    print(f"{name}: Array {massSolarArray(panel):.2f} kg (Array area : {areaSolarAray(panel):.2f}m^2), Battery {battery_weight():.2f} kg, PMD {pmd_mass(panel):.2f} kg, Total {total_eps_mass(panel):.2f} kg")

# EPS path losses; orbit energies already include the sizing margin. Simple calculations no special formulas. 
day_energy_lost=(energy_one_orbit-eclipse_energy)*(1-path_efficiency["day"]) # J/orbit
eclipse_energy_lost=eclipse_energy*(1-path_efficiency["eclipse"]) # J/orbit
energy_lost_one_orbit=day_energy_lost+eclipse_energy_lost # J
duration_one_orbit=durations["day"]+durations["eclipse"] # s
energy_lost_per_day=energy_lost_one_orbit*(24*60*60/duration_one_orbit) # J per 24 hours
average_power_lost=energy_lost_one_orbit/duration_one_orbit # W
print(f"EPS path energy lost per orbit: daylight {day_energy_lost*JtoWh:.2f} Wh, eclipse {eclipse_energy_lost*JtoWh:.2f} Wh")
print(f"EPS energy lost per 24-hour day: {energy_lost_per_day*JtoWh:.2f} Wh")
print(f"Average EPS power lost over one day: {day_energy_lost/durations['day']:.2f} W")
print(f"Average EPS power lost over one eclipse: {eclipse_energy_lost/durations['eclipse']:.2f} W")
print(f"Average EPS power lost over one orbit: {average_power_lost:.2f} W")



print("#########################")
print("#      RTG  Sizing      #")
print("#########################")


# RTG sizing
# Reader Table 45: thermal fuel specific power converted from W/g to W/kg.
# Specific costs are dollars per thermal watt, based on FY 1999 costs.
nuclear_isotopes = {
    "Plutonium_238": {"symbol": "Pu", "atomic_mass": 238, "thermal_W_per_kg": 550.0, "half_life_yr": 90.0, "cost_USD_per_W_thermal": 3000.0},
    "Polonium_210": {"symbol": "Po", "atomic_mass": 210, "thermal_W_per_kg": 141000.0, "half_life_yr": 0.38, "cost_USD_per_W_thermal": 570.0},
}

def p0Isotope(isotope):
    return peakPower*math.exp(math.log(2)*lengthofmission/isotope["half_life_yr"]) #Electrical W; Eq. 95

def massIsotope(isotope, thermal_to_electric_efficiency):
    # Specific power is THERMAL W/kg. This is isotope fuel mass only.
    return p0Isotope(isotope)/(thermal_to_electric_efficiency*isotope["thermal_W_per_kg"])

def massRTG(isotope, system_specific_power):
    # Eq. 96 requires whole-generator electrical W/kg; excludes external PMD.
    return p0Isotope(isotope)/system_specific_power

def total_rtg_system_mass(isotope, system_specific_power):
    # Same preliminary PMD fraction as solar EPS; sizing margin is already included.
    return massRTG(isotope, system_specific_power)/(1-pmd_mass_fraction)

def rtg_pmd_mass(isotope, system_specific_power):
    return pmd_mass_fraction*total_rtg_system_mass(isotope, system_specific_power)


gphs_efficiency=290/4234
for name,isotope in nuclear_isotopes.items():
    print(f"{name}: Required BOL electrical power {p0Isotope(isotope):.2f} W, Fuel mass at assumed GPHS efficiency {massIsotope(isotope,gphs_efficiency):.2f} kg")

# Reader p. 130: GPHS-RTG example, 290 electrical W, 4234 thermal W, 55 kg.
# Plutonium is the better choice, we are able to extrapolate the data from the example in the book.

gphs_specific_power=290/55
pu238=nuclear_isotopes["Plutonium_238"]
print(f"Pu-238 isotope fuel mass at GPHS reference efficiency: {massIsotope(pu238, gphs_efficiency):.2f} kg")
print(f"Pu-238 RTG mass at GPHS reference W/kg: {massRTG(pu238, gphs_specific_power):.2f} kg (excluding PMD)")
print(f"Pu-238 PMD mass: {rtg_pmd_mass(pu238, gphs_specific_power):.2f} kg")
print(f"Pu-238 total RTG system mass including PMD: {total_rtg_system_mass(pu238, gphs_specific_power):.2f} kg (includes {safety_margin:g}x sizing margin)")
