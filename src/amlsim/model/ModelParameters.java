package amlsim.model;

import java.io.*;
import java.util.Random;
import java.util.Properties;

import amlsim.AMLSim;
import amlsim.Account;

/**
 * Adjust transaction parameters for fine-tuning of the transaction network
 */
public class ModelParameters {

    private static Random rand = new Random(AMLSim.getSeed());
    private static Properties prop = null;

    private static float SAR2SAR_EDGE_THRESHOLD = 0.0F;
    private static float SAR2NORMAL_EDGE_THRESHOLD = 0.0F;
    private static float NORMAL2SAR_EDGE_THRESHOLD = 0.0F;
    private static float NORMAL2NORMAL_EDGE_THRESHOLD = 0.0F;

    private static float SAR2SAR_AMOUNT_RATIO = 1.0F;
    private static float SAR2NORMAL_AMOUNT_RATIO = 1.0F;
    private static float NORMAL2SAR_AMOUNT_RATIO = 1.0F;
    private static float NORMAL2NORMAL_AMOUNT_RATIO = 1.0F;

    private static float NORMAL_AMOUNT_MAX = 1.0F;  // Maximum ratio of transaction amount from normal accounts
    private static float NORMAL_TX_PROB = 1.0F;

    /**
     * Whether no adjustment parameters in this class will be applied for transactions
     * @return If true, all normal transactions are not affected by any adjustment parameters
     */
    public static boolean isUnused(){
        return prop == null;
    }

    private static float getRatio(String key){
        return Float.parseFloat(prop.getProperty(key, "1.0"));
    }

    public static void loadProperties(String propFile){
        if(propFile == null){
            return;
        }
        System.out.println("Model parameter file: " + propFile);
        try{
            prop = new Properties();
            prop.load(new FileInputStream(propFile));
        }catch (IOException e){
            System.err.println("Cannot load model parameter file: " + propFile);
            e.printStackTrace();
            prop = null;
            return;
        }

        SAR2SAR_EDGE_THRESHOLD = getRatio("sar2sar.edge.threshold");
        SAR2NORMAL_EDGE_THRESHOLD = getRatio("sar2normal.edge.threshold");
        NORMAL2SAR_EDGE_THRESHOLD = getRatio("normal2sar.edge.threshold");
        NORMAL2NORMAL_EDGE_THRESHOLD = getRatio("normal2normal.edge.threshold");

        SAR2SAR_AMOUNT_RATIO = getRatio("sar2sar.amount.ratio");
        SAR2NORMAL_AMOUNT_RATIO = getRatio("sar2normal.amount.ratio");
        NORMAL2SAR_AMOUNT_RATIO = getRatio("normal2sar.amount.ratio");
        NORMAL2NORMAL_AMOUNT_RATIO = getRatio("normal2normal.amount.ratio");

        NORMAL_AMOUNT_MAX = getRatio("normal.transaction.max");
        NORMAL_TX_PROB = getRatio("normal.transaction.prob");

        System.out.println("Transaction edge addition threshold (proportion of SAR accounts):");
        System.out.println("\tSAR -> SAR: " + SAR2SAR_EDGE_THRESHOLD);
        System.out.println("\tSAR -> Normal: " + SAR2NORMAL_EDGE_THRESHOLD);
        System.out.println("\tSAR -> SAR: " + NORMAL2SAR_EDGE_THRESHOLD);
        System.out.println("\tNormal -> Normal: " + NORMAL2NORMAL_EDGE_THRESHOLD);
        System.out.println("Transaction amount ratio:");
        System.out.println("\tSAR -> SAR: " + SAR2SAR_AMOUNT_RATIO);
        System.out.println("\tSAR -> Normal: " + SAR2NORMAL_AMOUNT_RATIO);
        System.out.println("\tNormal -> SAR: " + NORMAL2SAR_AMOUNT_RATIO);
        System.out.println("\tNormal -> Normal: " + NORMAL2NORMAL_AMOUNT_RATIO);
    }

    /**
     * Generate an up to 10% ratio noise for the base transaction amount
     * @return Amount ratio [0.9, 1.1]
     */
    public static float generateAmountRatio(){  // [0.9, 1.1]
        return rand.nextFloat() * 0.2F + 0.9F;
    }

    /**
     * Adjust transaction amount from the given accounts and the base amount
     * @param orig Originator account
     * @param bene Beneficiary account
     * @param baseAmount Base amount
     * @return Adjusted amount (If it should not make this transaction, return non-positive value)
     */
    public static float adjustAmount(Account orig, Account bene, float baseAmount){
        // Generate decentralized amount with up to 10% noise
        float amount = baseAmount * generateAmountRatio();

        if(isUnused()){
            return amount;
        }

        float ratio;
        if(orig.isSAR()){  // SAR originator
            if(bene.isSAR()){  // SAR -> SAR
                ratio = SAR2SAR_AMOUNT_RATIO;
            }else{  // SAR -> Normal
                ratio = SAR2NORMAL_AMOUNT_RATIO;
            }
        }else{  // Normal originator
            if(bene.isSAR()){  // Normal -> SAR
                ratio = NORMAL2SAR_AMOUNT_RATIO;
            }else{  // Normal -> Normal
                ratio = NORMAL2NORMAL_AMOUNT_RATIO;
            }

            // TODO: Load the following additional parameters from the same Java property file
            float actionID = rand.nextFloat();
            if(actionID < 0.05){  // High-amount payment transaction (near to the upper limit) with 5% of the time
                ratio *= NORMAL_AMOUNT_MAX;
            }else if(actionID < NORMAL_TX_PROB){  // Half-amount transaction with 45% of the time
                ratio *= 0.5F;
            }else{
                ratio *= 0;  // Skip transaction with 50% of the time
            }
        }
        return amount * ratio;
    }

    /**
     * Determine whether the transaction edge should be actually added between the given accounts
     * @param orig Originator account
     * @param bene Beneficiary account
     * @return If the transaction should be actually added, return true.
     */
    public static boolean shouldAddEdge(Account orig, Account bene){
        if(isUnused()){  // Add this edge without qualification
            return true;
        }
        // Proportion of SAR beneficiary accounts of the originator account
        float benePropThreshold = SAR2NORMAL_EDGE_THRESHOLD;
        int beneNumThreshold = (int) Math.floor(1 / NORMAL2SAR_EDGE_THRESHOLD);

        int numNeighbors = orig.getBeneList().size();
        float propSARBene = orig.getPropSARBene();

        if(orig.isSAR()){  // SAR originator
            if(bene.isSAR()){  // SAR -> SAR
                return propSARBene >= SAR2SAR_EDGE_THRESHOLD;
            }else{  // SAR -> Normal
                // Allow edge creations if the ratio of SAR beneficiary accounts is enough large
                return propSARBene >= SAR2NORMAL_EDGE_THRESHOLD;
            }
        }else{  // Normal originator
            if(bene.isSAR()){  // Normal -> SAR
                // Create a transaction edge if the ratio of SAR beneficiary accounts is still large
                if(NORMAL2SAR_EDGE_THRESHOLD <= 0.0F){
                    return true;
                }
                return numNeighbors > (int) Math.floor(1 / NORMAL2SAR_EDGE_THRESHOLD);
//                        && propSARBene >= NORMAL2SAR_EDGE_THRESHOLD;
            }else{  // Normal -> Normal
                return propSARBene >= NORMAL2NORMAL_EDGE_THRESHOLD;
            }
        }
    }

}
