"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const common_token_1 = require("./common-token");
describe('common-token', () => {
    it(`will verify PAREN_START`, () => {
        const text = 'Hello, my (beautiful) world!';
        const textZero = 'Hello, my beautiful world!';
        const regex = new RegExp(common_token_1.COMMON_TOKEN.PAREN_START.PATTERN);
        expect(text.match(regex).length).toBeGreaterThan(0);
        expect(textZero.match(regex)).toBeNull();
    });
    it(`will verify PAREN_END`, () => {
        const text = 'Hello, my (beautiful) world!';
        const textZero = 'Hello, my beautiful world!';
        const regex = new RegExp(common_token_1.COMMON_TOKEN.PAREN_END.PATTERN);
        expect(text.match(regex).length).toBeGreaterThan(0);
        expect(textZero.match(regex)).toBeNull();
    });
});
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiY29tbW9uLXRva2VuLnNwZWMuanMiLCJzb3VyY2VSb290IjoiIiwic291cmNlcyI6WyIuLi8uLi8uLi8uLi9zcmMvbGliL3BhcnNlci9jb21tb24tdG9rZW4uc3BlYy50cyJdLCJuYW1lcyI6W10sIm1hcHBpbmdzIjoiOztBQUFBLGlEQUE4QztBQUU5QyxRQUFRLENBQUMsY0FBYyxFQUFFLEdBQUcsRUFBRTtJQUM1QixFQUFFLENBQUMseUJBQXlCLEVBQUUsR0FBRyxFQUFFO1FBQ2pDLE1BQU0sSUFBSSxHQUFHLDhCQUE4QixDQUFDO1FBQzVDLE1BQU0sUUFBUSxHQUFHLDRCQUE0QixDQUFDO1FBQzlDLE1BQU0sS0FBSyxHQUFHLElBQUksTUFBTSxDQUFDLDJCQUFZLENBQUMsV0FBVyxDQUFDLE9BQWMsQ0FBQyxDQUFDO1FBQ2xFLE1BQU0sQ0FBQyxJQUFJLENBQUMsS0FBSyxDQUFDLEtBQUssQ0FBQyxDQUFDLE1BQU0sQ0FBQyxDQUFDLGVBQWUsQ0FBQyxDQUFDLENBQUMsQ0FBQztRQUNwRCxNQUFNLENBQUMsUUFBUSxDQUFDLEtBQUssQ0FBQyxLQUFLLENBQUMsQ0FBQyxDQUFDLFFBQVEsRUFBRSxDQUFDO0lBQzNDLENBQUMsQ0FBQyxDQUFDO0lBQ0gsRUFBRSxDQUFDLHVCQUF1QixFQUFFLEdBQUcsRUFBRTtRQUMvQixNQUFNLElBQUksR0FBRyw4QkFBOEIsQ0FBQztRQUM1QyxNQUFNLFFBQVEsR0FBRyw0QkFBNEIsQ0FBQztRQUM5QyxNQUFNLEtBQUssR0FBRyxJQUFJLE1BQU0sQ0FBQywyQkFBWSxDQUFDLFNBQVMsQ0FBQyxPQUFjLENBQUMsQ0FBQztRQUNoRSxNQUFNLENBQUMsSUFBSSxDQUFDLEtBQUssQ0FBQyxLQUFLLENBQUMsQ0FBQyxNQUFNLENBQUMsQ0FBQyxlQUFlLENBQUMsQ0FBQyxDQUFDLENBQUM7UUFDcEQsTUFBTSxDQUFDLFFBQVEsQ0FBQyxLQUFLLENBQUMsS0FBSyxDQUFDLENBQUMsQ0FBQyxRQUFRLEVBQUUsQ0FBQztJQUMzQyxDQUFDLENBQUMsQ0FBQztBQUNMLENBQUMsQ0FBQyxDQUFDIn0=