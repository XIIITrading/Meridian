export function validatePassword(p) {
    let error = '';
    const hint = null;
    let valid = true;
    if (!p) {
        error = 'At least 8 letters';
        // error = t('msg.error.signUpRules.completeRuleSet');
        valid = false;
    }
    else {
        if (!(p.length >= 8)) {
            error += 'At least 8 letters. ';
            // error += t('msg.error.signUpRules.atLeast8Char');
            valid = false;
        }
    }
    return { error, valid, hint };
}
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoicGFzc3dvcmRIZWxwZXJzLmpzIiwic291cmNlUm9vdCI6IiIsInNvdXJjZXMiOlsiLi4vLi4vLi4vc3JjL2xpYi9wYXNzd29yZEhlbHBlcnMudHMiXSwibmFtZXMiOltdLCJtYXBwaW5ncyI6IkFBQUEsTUFBTSxVQUFVLGdCQUFnQixDQUFDLENBQUM7SUFDaEMsSUFBSSxLQUFLLEdBQUcsRUFBRSxDQUFDO0lBQ2YsTUFBTSxJQUFJLEdBQUcsSUFBSSxDQUFDO0lBQ2xCLElBQUksS0FBSyxHQUFHLElBQUksQ0FBQztJQUVqQixJQUFJLENBQUMsQ0FBQyxFQUFFLENBQUM7UUFDUCxLQUFLLEdBQUcsb0JBQW9CLENBQUM7UUFDN0Isc0RBQXNEO1FBQ3RELEtBQUssR0FBRyxLQUFLLENBQUM7SUFDaEIsQ0FBQztTQUFNLENBQUM7UUFDTixJQUFJLENBQUMsQ0FBQyxDQUFDLENBQUMsTUFBTSxJQUFJLENBQUMsQ0FBQyxFQUFFLENBQUM7WUFDckIsS0FBSyxJQUFJLHNCQUFzQixDQUFDO1lBQ2hDLG9EQUFvRDtZQUNwRCxLQUFLLEdBQUcsS0FBSyxDQUFDO1FBQ2hCLENBQUM7SUFDSCxDQUFDO0lBQ0QsT0FBTyxFQUFFLEtBQUssRUFBRSxLQUFLLEVBQUUsSUFBSSxFQUFFLENBQUM7QUFDaEMsQ0FBQyJ9