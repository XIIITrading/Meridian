"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const decimal_1 = require("./decimal");
describe('decimal-utils', () => {
    describe('extractDecimalFromString', () => {
        it('will extract from alnum string', () => {
            const sourceText = 'USD $ 123456.001231 Hello World';
            const expected = '123456.001231';
            const result = (0, decimal_1.extractDecimalFromString)(sourceText);
            expect(result).toBe(expected);
        });
        it('will remove 2nd and more occurrence of decimal point', () => {
            const sourceText = '123.456.0-01.231';
            const expected = '123.456001231';
            const result = (0, decimal_1.extractDecimalFromString)(sourceText);
            expect(result).toBe(expected);
        });
        it('will extract valid minus value', () => {
            const sourceText = '-123.456.001.231';
            const expected = '-123.456001231';
            const result = (0, decimal_1.extractDecimalFromString)(sourceText);
            expect(result).toBe(expected);
        });
    });
    describe('composeNewDecimalValue', () => {
        it('will paste from the start', () => {
            const oldValue = '333';
            const sourceText = 'USD $ 111.111 Hello World';
            const expected = '111.111333';
            const result = (0, decimal_1.composeNewDecimalValue)({
                selectionStart: 0,
                selectionEnd: 0,
                newValue: sourceText,
                lastValue: oldValue,
            });
            expect(result).toBe(expected);
        });
        it('will paste from the end', () => {
            const oldValue = '333';
            const sourceText = 'USD $ -111.111 Hello World';
            const expected = '333111.111';
            const result = (0, decimal_1.composeNewDecimalValue)({
                selectionStart: 3,
                selectionEnd: 3,
                newValue: sourceText,
                lastValue: oldValue,
            });
            expect(result).toBe(expected);
        });
        it('will paste from the middle', () => {
            const oldValue = '333444';
            const sourceText = 'USD $ -111.111 Hello World';
            const expected = '33111.11144';
            const result = (0, decimal_1.composeNewDecimalValue)({
                selectionStart: 2,
                selectionEnd: 4,
                newValue: sourceText,
                lastValue: oldValue,
            });
            expect(result).toBe(expected);
        });
        it('will paste from the start negative', () => {
            const oldValue = '333';
            const sourceText = 'USD $ -111.111 Hello World';
            const expected = '-111.111333';
            const result = (0, decimal_1.composeNewDecimalValue)({
                selectionStart: 0,
                selectionEnd: 0,
                newValue: sourceText,
                lastValue: oldValue,
            });
            expect(result).toBe(expected);
        });
        it('will paste from the middle part 2', () => {
            const oldValue = '33.3444';
            const sourceText = 'USD $ 111.111 Hello World';
            const expected = '33.11111144';
            const result = (0, decimal_1.composeNewDecimalValue)({
                selectionStart: 3,
                selectionEnd: 5,
                newValue: sourceText,
                lastValue: oldValue,
            });
            expect(result).toBe(expected);
        });
    });
});
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiZGVjaW1hbC5zcGVjLmpzIiwic291cmNlUm9vdCI6IiIsInNvdXJjZXMiOlsiLi4vLi4vLi4vLi4vLi4vc3JjL2xpYi9jb2x1bW5IZWxwZXIvdXRpbHMvZGVjaW1hbC5zcGVjLnRzIl0sIm5hbWVzIjpbXSwibWFwcGluZ3MiOiI7O0FBQUEsdUNBQTZFO0FBRTdFLFFBQVEsQ0FBQyxlQUFlLEVBQUUsR0FBRyxFQUFFO0lBQzdCLFFBQVEsQ0FBQywwQkFBMEIsRUFBRSxHQUFHLEVBQUU7UUFDeEMsRUFBRSxDQUFDLGdDQUFnQyxFQUFFLEdBQUcsRUFBRTtZQUN4QyxNQUFNLFVBQVUsR0FBRyxpQ0FBaUMsQ0FBQztZQUNyRCxNQUFNLFFBQVEsR0FBRyxlQUFlLENBQUM7WUFDakMsTUFBTSxNQUFNLEdBQUcsSUFBQSxrQ0FBd0IsRUFBQyxVQUFVLENBQUMsQ0FBQztZQUNwRCxNQUFNLENBQUMsTUFBTSxDQUFDLENBQUMsSUFBSSxDQUFDLFFBQVEsQ0FBQyxDQUFDO1FBQ2hDLENBQUMsQ0FBQyxDQUFDO1FBQ0gsRUFBRSxDQUFDLHNEQUFzRCxFQUFFLEdBQUcsRUFBRTtZQUM5RCxNQUFNLFVBQVUsR0FBRyxrQkFBa0IsQ0FBQztZQUN0QyxNQUFNLFFBQVEsR0FBRyxlQUFlLENBQUM7WUFDakMsTUFBTSxNQUFNLEdBQUcsSUFBQSxrQ0FBd0IsRUFBQyxVQUFVLENBQUMsQ0FBQztZQUNwRCxNQUFNLENBQUMsTUFBTSxDQUFDLENBQUMsSUFBSSxDQUFDLFFBQVEsQ0FBQyxDQUFDO1FBQ2hDLENBQUMsQ0FBQyxDQUFDO1FBQ0gsRUFBRSxDQUFDLGdDQUFnQyxFQUFFLEdBQUcsRUFBRTtZQUN4QyxNQUFNLFVBQVUsR0FBRyxrQkFBa0IsQ0FBQztZQUN0QyxNQUFNLFFBQVEsR0FBRyxnQkFBZ0IsQ0FBQztZQUNsQyxNQUFNLE1BQU0sR0FBRyxJQUFBLGtDQUF3QixFQUFDLFVBQVUsQ0FBQyxDQUFDO1lBQ3BELE1BQU0sQ0FBQyxNQUFNLENBQUMsQ0FBQyxJQUFJLENBQUMsUUFB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