"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ComputedTypePasteError = void 0;
const type_conversion_error_1 = require("./type-conversion.error");
class ComputedTypePasteError extends type_conversion_error_1.TypeConversionError {
    constructor() {
        super('Paste operation is not supported on the active cell');
    }
}
exports.ComputedTypePasteError = ComputedTypePasteError;
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiY29tcHV0ZWQtdHlwZS1wYXN0ZS5lcnJvci5qcyIsInNvdXJjZVJvb3QiOiIiLCJzb3VyY2VzIjpbIi4uLy4uLy4uLy4uL3NyYy9saWIvZXJyb3IvY29tcHV0ZWQtdHlwZS1wYXN0ZS5lcnJvci50cyJdLCJuYW1lcyI6W10sIm1hcHBpbmdzIjoiOzs7QUFBQSxtRUFBOEQ7QUFFOUQsTUFBYSxzQkFBdUIsU0FBUSwyQ0FBbUI7SUFDN0Q7UUFDRSxLQUFLLENBQUMscURBQXFELENBQUMsQ0FBQztJQUMvRCxDQUFDO0NBQ0Y7QUFKRCx3REFJQyJ9