"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.latLongToJoinedString = exports.convertGeoNumberToString = void 0;
const convertGeoNumberToString = (val) => {
    return val.toFixed(10).replace(/\.0+$|(\.[^0]*)0+$/, '$1');
};
exports.convertGeoNumberToString = convertGeoNumberToString;
const latLongToJoinedString = (lat, long) => [lat, long].map((k) => (0, exports.convertGeoNumberToString)(k)).join(';');
exports.latLongToJoinedString = latLongToJoinedString;
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiZ2VvRGF0YVV0aWxzLmpzIiwic291cmNlUm9vdCI6IiIsInNvdXJjZXMiOlsiLi4vLi4vLi4vc3JjL2xpYi9nZW9EYXRhVXRpbHMudHMiXSwibmFtZXMiOltdLCJtYXBwaW5ncyI6Ijs7O0FBQU8sTUFBTSx3QkFBd0IsR0FBRyxDQUFDLEdBQVcsRUFBRSxFQUFFO0lBQ3RELE9BQU8sR0FBRyxDQUFDLE9BQU8sQ0FBQyxFQUFFLENBQUMsQ0FBQyxPQUFPLENBQUMsb0JBQW9CLEVBQUUsSUFBSSxDQUFDLENBQUM7QUFDN0QsQ0FBQyxDQUFDO0FBRlcsUUFBQSx3QkFBd0IsNEJBRW5DO0FBRUssTUFBTSxxQkFBcUIsR0FBRyxDQUFDLEdBQVcsRUFBRSxJQUFZLEVBQUUsRUFBRSxDQUNqRSxDQUFDLEdBQUcsRUFBRSxJQUFJLENBQUMsQ0FBQyxHQUFHLENBQUMsQ0FBQyxDQUFDLEVBQUUsRUFBRSxDQUFDLElBQUEsZ0NBQXdCLEVBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxJQUFJLENBQUMsR0FBRyxDQUFDLENBQUM7QUFEbkQsUUFBQSxxQkFBcUIseUJBQzhCIn0=