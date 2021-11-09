package amlsim;
import java.util.Random;

public class TargetedTransactionAmount {

   private SimProperties simProperties;
   private Random random;
   private double target;

   public TargetedTransactionAmount(Number target, Random random) {
       this.simProperties = AMLSim.getSimProp();
       this.random = random;
       this.target = target.doubleValue();
   }

   public double doubleValue() {
       double minTransactionAmount = simProperties.getMinTransactionAmount();
       double maxTransactionAmount = simProperties.getMaxTransactionAmount();
       double min, max, result;
       
       if (this.target < maxTransactionAmount) {
           max = this.target;
       }
       else {
           max = maxTransactionAmount;
       }
       
       if (this.target < minTransactionAmount) {
           min = this.target;
       }
       else {
           min = minTransactionAmount;
       }
 
       if (max - min <= 0)
       {
           result = this.target;
       }
       if (this.target - min <= 100)
       {
           result = this.target;
       }
       else
       {
           result =  min + random.nextDouble() * (max - min);
       }
       return result;
    }
}
