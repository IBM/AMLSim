package amlsim;

/**
 * A branch of a bank
 * In cash transactions, this class perform like an account
 */
public class Branch extends Account {

    private int id;  // Branch identifier
    private float limitAmount = 100.0F;  // Limit of deposit/withdrawal amount

    public Branch(int id){
        this.id = id;
    }

    /**
     * Get the limit of deposit/withdrawal amount
     * @return Limit of deposit/withdrawal amount
     */
    public float getLimitAmount(){
        return limitAmount;
    }

    /**
     * Get the branch identifier as String
     * @return Branch identifier
     */
    public String toString(){
        return "B" + this.id;
    }

    /**
     * Get the branch identifier as String
     * @return Branch identifier
     */
    public String getName() {
        return toString();
    }

}
