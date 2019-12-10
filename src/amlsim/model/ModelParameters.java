package amlsim.model;

import java.util.Random;

import amlsim.AMLSim;
import amlsim.Account;

/**
 * Adjust transaction parameters for fine-tuning of the transaction network
 */
public class ModelParameters {

    private static Random rand = new Random(AMLSim.getSeed());
    private static boolean enabled = Boolean.parseBoolean(System.getProperty("amlsim.param", "true"));

    public static void setEnabled(boolean flag){
        enabled = flag;
    }

    public static boolean isEnabled(){
        return enabled;
    }

    public static float computeAmount(Account orig, Account bene, float baseAmount){
        if(!enabled){
            return baseAmount;
        }
        // TODO: Make the following parameters customizable from command lines as Java system properties
        float ratio = 1.0F;
        if(orig.isSAR()){  // SAR originator
            if(bene.isSAR()){  // SAR -> SAR
                ratio = 2.0F;
            }else{  // SAR -> Normal
//                ratio = 1.0F;
            }
        }else{  // Normal originator
            int actionID = rand.nextInt(100);
            if(actionID < 5){  // High-amount payment transaction (near to the upper limit) with 5% of the time
                ratio = 30;
            }else if(actionID < 50){  // Half-amount transaction with 45% of the time
                ratio = 0.5F;
            }else{
                ratio = 0;  // Skip transaction with 50% of the time
            }
        }
        return baseAmount * ratio;
    }

    public static boolean shouldAddEdge(Account orig, Account bene){
        if(!enabled){
            return true;
        }
        // TODO: Make the following parameters customizable from command lines as Java system properties
        if(orig.isSAR()){  // SAR originator
            if(bene.isSAR()){  // SAR -> SAR
                return true;
            }else{  // SAR -> Normal
                int numNeighbors = orig.getBeneList().size();
                return numNeighbors < 100000;
            }
        }else{
            return true;
        }
    }

}
