Now that it is compiles/*
    CONFLUENCE ZONES ACSIL STUDY - HEADER FILE
    
    Function declarations and structures for the Confluence Zones study
    
    Author: XIII Trading Systems
    Version: 1.0.0
*/

#ifndef CONFLUENCE_ZONES_H
#define CONFLUENCE_ZONES_H

#include "sierrachart.h"
#include <vector>
#include <string>

// Forward declarations
struct ConfluenceZone;

/*==========================================================================*/
// Function Prototypes
/*==========================================================================*/

// Main study function
SCSFExport scsf_ConfluenceZones(SCStudyInterfaceRef sc);

// Zone file loading and parsing
void LoadZonesFromFile(SCStudyInterfaceRef sc, const SCString& filePath, 
                      std::vector<ConfluenceZone>& zones);

bool ParseZoneFromJson(const std::string& jsonStr, ConfluenceZone& zone);

// JSON parsing helpers
float ExtractFloatValue(const std::string& json, const std::string& key);
SCString ExtractStringValue(const std::string& json, const std::string& key);

// Drawing functions  
void DrawConfluenceZones(SCStudyInterfaceRef sc, const std::vector<ConfluenceZone>& zones,
                        bool showLabels, int transparency, float minScore,
                        bool showL1, bool showL2, bool showL3, bool showL4, bool showL5);

void ClearZoneDrawings(SCStudyInterfaceRef sc);

/*==========================================================================*/
// Zone Data Structure
/*==========================================================================*/

struct ConfluenceZone {
    float High;
    float Low;
    float Center;
    float Score;
    int SourceCount;
    float ColorIntensity;
    int ZoneId;
    COLORREF Color;
    SCString Level;
    bool IsValid;
    
    ConfluenceZone();
};

/*==========================================================================*/
// Constants and Definitions
/*==========================================================================*/

// Zone level definitions
#define ZONE_L1 1
#define ZONE_L2 2  
#define ZONE_L3 3
#define ZONE_L4 4
#define ZONE_L5 5

// Default color definitions (match Python config)
#define COLOR_L1 RGB(128, 128, 128)  // Gray
#define COLOR_L2 RGB(0, 128, 255)    // Blue
#define COLOR_L3 RGB(0, 200, 0)      // Green
#define COLOR_L4 RGB(255, 128, 0)    // Orange
#define COLOR_L5 RGB(255, 0, 0)      // Red

// Drawing line number ranges
#define ZONE_RECTANGLE_BASE 1000
#define ZONE_LABEL_BASE 2000

// File refresh settings
#define MIN_REFRESH_INTERVAL 5    // Minimum 5 seconds
#define MAX_REFRESH_INTERVAL 300  // Maximum 5 minutes
#define DEFAULT_REFRESH_INTERVAL 30 // Default 30 seconds

#endif // CONFLUENCE_ZONES_H