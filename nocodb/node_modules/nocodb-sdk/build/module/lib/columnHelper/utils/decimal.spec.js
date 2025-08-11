import { composeNewDecimalValue, extractDecimalFromString } from './decimal';
describe('decimal-utils', () => {
    describe('extractDecimalFromString', () => {
        it('will extract from alnum string', () => {
            const sourceText = 'USD $ 123456.001231 Hello World';
            const expected = '123456.001231';
            const result = extractDecimalFromString(sourceText);
            expect(result).toBe(expected);
        });
        it('will remove 2nd and more occurrence of decimal point', () => {
            const sourceText = '123.456.0-01.231';
            const expected = '123.456001231';
            const result = extractDecimalFromString(sourceText);
            expect(result).toBe(expected);
        });
        it('will extract valid minus value', () => {
            const sourceText = '-123.456.001.231';
            const expected = '-123.456001231';
            const result = extractDecimalFromString(sourceText);
            expect(result).toBe(expected);
        });
    });
    describe('composeNewDecimalValue', () => {
        it('will paste from the start', () => {
            const oldValue = '333';
            const sourceText = 'USD $ 111.111 Hello World';
            const expected = '111.111333';
            const result = composeNewDecimalValue({
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
            const result = composeNewDecimalValue({
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
            const result = composeNewDecimalValue({
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
            const result = composeNewDecimalValue({
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
            const result = composeNewDecimalValue({
                selectionStart: 3,
                selectionEnd: 5,
                newValue: sourceText,
                lastValue: oldValue,
            });
            expect(result).toBe(expected);
        });
    });
});
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiZGVjaW1hbC5zcGVjLmpzIiwic291cmNlUm9vdCI6IiIsInNvdXJjZXMiOlsiLi4vLi4vLi4vLi4vLi4vc3JjL2xpYi9jb2x1bW5IZWxwZXIvdXRpbHMvZGVjaW1hbC5zcGVjLnRzIl0sIm5hbWVzIjpbXSwibWFwcGluZ3MiOiJBQUFBLE9BQU8sRUFBRSxzQkFBc0IsRUFBRSx3QkFBd0IsRUFBRSxNQUFNLFdBQVcsQ0FBQztBQUU3RSxRQUFRLENBQUMsZUFBZSxFQUFFLEdBQUcsRUFBRTtJQUM3QixRQUFRLENBQUMsMEJBQTBCLEVBQUUsR0FBRyxFQUFFO1FBQ3hDLEVBQUUsQ0FBQyxnQ0FBZ0MsRUFBRSxHQUFHLEVBQUU7WUFDeEMsTUFBTSxVQUFVLEdBQUcsaUNBQWlDLENBQUM7WUFDckQsTUFBTSxRQUFRLEdBQUcsZUFBZSxDQUFDO1lBQ2pDLE1BQU0sTUFBTSxHQUFHLHdCQUF3QixDQUFDLFVBQVUsQ0FBQyxDQUFDO1lBQ3BELE1BQU0sQ0FBQyxNQUFNLENBQUMsQ0FBQyxJQUFJLENBQUMsUUFBUSxDQUFDLENBQUM7UUFDaEMsQ0FBQyxDQUFDLENBQUM7UUFDSCxFQUFFLENBQUMsc0RBQXNELEVBQUUsR0FBRyxFQUFFO1lBQzlELE1BQU0sVUFBVSxHQUFHLGtCQUFrQixDQUFDO1lBQ3RDLE1BQU0sUUFBUSxHQUFHLGVBQWUsQ0FBQztZQUNqQyxNQUFNLE1BQU0sR0FBRyx3QkFBd0IsQ0FBQyxVQUFVLENBQUMsQ0FBQztZQUNwRCxNQUFNLENBQUMsTUFBTSxDQUFDLENBQUMsSUFBSSxDQUFDLFFBQVEsQ0FBQyxDQUFDO1FBQ2hDLENBQUMsQ0FBQyxDQUFDO1FBQ0gsRUFBRSxDQUFDLGdDQUFnQyxFQUFFLEdBQUcsRUFBRTtZQUN4QyxNQUFNLFVBQVUsR0FBRyxrQkFBa0IsQ0FBQztZQUN0QyxNQUFNLFFBQVEsR0FBRyxnQkFBZ0IsQ0FBQztZQUNsQyxNQUFNLE1BQU0sR0FBRyx3QkFBd0IsQ0FBQyxVQUFVLENBQUMsQ0FBQztZQUNwRCxNQUFNLENBQUMsTUFB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