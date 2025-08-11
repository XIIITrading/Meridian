import { TypeConversionError } from './type-conversion.error';
export class SelectTypeConversionError extends TypeConversionError {
    constructor(value, missingOptions) {
        super('');
        this.value = value;
        this.missingOptions = missingOptions;
        this.isErrorSuppressed = true;
    }
}
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoic2VsZWN0LXR5cGUtY29udmVyc2lvbi5lcnJvci5qcyIsInNvdXJjZVJvb3QiOiIiLCJzb3VyY2VzIjpbIi4uLy4uLy4uLy4uL3NyYy9saWIvZXJyb3Ivc2VsZWN0LXR5cGUtY29udmVyc2lvbi5lcnJvci50cyJdLCJuYW1lcyI6W10sIm1hcHBpbmdzIjoiQUFDQSxPQUFPLEVBQUUsbUJBQW1CLEVBQUUsTUFBTSx5QkFBeUIsQ0FBQztBQUU5RCxNQUFNLE9BQU8seUJBQ1gsU0FBUSxtQkFBbUI7SUFHM0IsWUFBcUIsS0FBZSxFQUFXLGNBQXdCO1FBQ3JFLEtBQUssQ0FBQyxFQUFFLENBQUMsQ0FBQztRQURTLFVBQUssR0FBTCxLQUFLLENBQVU7UUFBVyxtQkFBYyxHQUFkLGNBQWMsQ0FBVTtRQUVyRSxJQUFJLENBQUMsaUJBQWlCLEdBQUcsSUFBSSxDQUFDO0lBQ2hDLENBQUM7Q0FHRiJ9