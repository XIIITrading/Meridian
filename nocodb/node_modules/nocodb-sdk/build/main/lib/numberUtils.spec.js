"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const numberUtils_1 = require("./numberUtils");
describe('numberUtils', () => {
    describe('numberize', () => {
        it('will be null when null is provided', () => {
            expect((0, numberUtils_1.numberize)(null)).toBeNull();
        });
        it('will be undefined when undefined is provided', () => {
            expect((0, numberUtils_1.numberize)(undefined)).toBeUndefined();
        });
        it('will be undefined when word is provided', () => {
            expect((0, numberUtils_1.numberize)('hello')).toBeUndefined();
        });
        it('will be number when number string is provided', () => {
            expect((0, numberUtils_1.numberize)('873')).toBe(873);
        });
        it('will be number when number is provided', () => {
            expect((0, numberUtils_1.numberize)(873)).toBe(873);
        });
    });
});
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoibnVtYmVyVXRpbHMuc3BlYy5qcyIsInNvdXJjZVJvb3QiOiIiLCJzb3VyY2VzIjpbIi4uLy4uLy4uL3NyYy9saWIvbnVtYmVyVXRpbHMuc3BlYy50cyJdLCJuYW1lcyI6W10sIm1hcHBpbmdzIjoiOztBQUFBLCtDQUEwQztBQUUxQyxRQUFRLENBQUMsYUFBYSxFQUFFLEdBQUcsRUFBRTtJQUMzQixRQUFRLENBQUMsV0FBVyxFQUFFLEdBQUcsRUFBRTtRQUN6QixFQUFFLENBQUMsb0NBQW9DLEVBQUUsR0FBRyxFQUFFO1lBQzVDLE1BQU0sQ0FBQyxJQUFBLHVCQUFTLEVBQUMsSUFBSSxDQUFDLENBQUMsQ0FBQyxRQUFRLEVBQUUsQ0FBQztRQUNyQyxDQUFDLENBQUMsQ0FBQztRQUNILEVBQUUsQ0FBQyw4Q0FBOEMsRUFBRSxHQUFHLEVBQUU7WUFDdEQsTUFBTSxDQUFDLElBQUEsdUJBQVMsRUFBQyxTQUFTLENBQUMsQ0FBQyxDQUFDLGFBQWEsRUFBRSxDQUFDO1FBQy9DLENBQUMsQ0FBQyxDQUFDO1FBQ0gsRUFBRSxDQUFDLHlDQUF5QyxFQUFFLEdBQUcsRUFBRTtZQUNqRCxNQUFNLENBQUMsSUFBQSx1QkFBUyxFQUFDLE9BQU8sQ0FBQyxDQUFDLENBQUMsYUFBYSxFQUFFLENBQUM7UUFDN0MsQ0FBQyxDQUFDLENBQUM7UUFDSCxFQUFFLENBQUMsK0NBQStDLEVBQUUsR0FBRyxFQUFFO1lBQ3ZELE1BQU0sQ0FBQyxJQUFBLHVCQUFTLEVBQUMsS0FBSyxDQUFDLENBQUMsQ0FBQyxJQUFJLENBQUMsR0FBRyxDQUFDLENBQUM7UUFDckMsQ0FBQyxDQUFDLENBQUM7UUFDSCxFQUFFLENBQUMsd0NBQXdDLEVBQUUsR0FBRyxFQUFFO1lBQ2hELE1BQU0sQ0FBQyxJQUFBLHVCQUFTLEVBQUMsR0FBRyxDQUFDLENBQUMsQ0FBQyxJQUFJLENBQUMsR0FBRyxDQUFDLENBQUM7UUFDbkMsQ0FBQyxDQUFDLENBQUM7SUFDTCxDQUFDLENBQUMsQ0FBQztBQUNMLENBQUMsQ0FBQyxDQUFDIn0=