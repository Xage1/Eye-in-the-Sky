package com.eye.sky.net

/**
 * Exact mirror of skyController.get_full_sky_scene() response.
 *
 * Top-level keys: timestamp, observer, pointing, stars, planets,
 *   constellation, moon_phase, iss, satellites, events, visibility
 */
data class SkySceneResp(
    val timestamp:     String?,
    val observer:      ObserverInfo?,
    val pointing:      PointingInfo?,
    val stars:         List<StarDto>?,
    val planets:       List<PlanetDto>?,
    val constellation: ConstellationDto?,
    val moon_phase:    MoonPhaseDto?,
    val iss:           IssDto?,
    val satellites:    List<SatelliteDto>?,
    val events:        Any?,
    val visibility:    Any?,
)

data class ObserverInfo(
    val lat: Double,
    val lon: Double,
)

data class PointingInfo(
    val azimuth_deg:  Double,
    val altitude_deg: Double,
    val roll_deg:     Double,
)

/** One star from get_visible_stars() */
data class StarDto(
    val name:           String?,
    val constellation:  String?,
    val magnitude:      Double,
    val ra:             Double,
    val dec:            Double,
    val altitude_deg:   Double,
    val azimuth_deg:    Double,
    val screen_x:       Double?,
    val screen_y:       Double?,
    val distance_from_centre_deg: Double?,
)

/** One planet from get_planet_positions() */
data class PlanetDto(
    val name:         String,
    val altitude_deg: Double,
    val azimuth_deg:  Double,
    val screen_x:     Double?,
    val screen_y:     Double?,
    val ra_deg:       Double?,
    val dec_deg:      Double?,
)

/** Moon phase from get_moon_phase_local() — nested under moon_phase key */
data class MoonPhaseDto(
    val phase_name:         String?,
    val age_days:           Double?,
    val illumination_pct:   Double?,
    val synodic_month_days: Double?,
)

/** ISS from get_iss_position() */
data class IssDto(
    val latitude:     Double?,
    val longitude:    Double?,
    val altitude_deg: Double?,
    val azimuth_deg:  Double?,
    val visible:      Boolean?,
    val timestamp:    Long?,
    val error:        String?,
)

/** Satellite from satellite_service.get_visible_satellites() */
data class SatelliteDto(
    val name:         String,
    val altitude_deg: Double?,
    val azimuth_deg:  Double?,
)

/** Closest constellation from get_closest_constellation() */
data class ConstellationDto(
    val name:           String?,
    val description:    String?,
    val myth:           String?,
    val discoverer:     String?,
    val year:           String?,
    val brightest_star: String?,
    val major_stars:    List<String>?,
    val altitude_deg:   Double?,
    val azimuth_deg:    Double?,
    val separation_deg: Double?,
    val centroid_ra:    Double?,
    val centroid_dec:   Double?,
)

/** Response from /starmap/ endpoint */
data class StarMapResp(
    val stars:          List<Any>?,
    val constellations: List<Any>?,
)

/** Paystack plans response */
data class PlansResp(val plans: Map<String, Any?>?)