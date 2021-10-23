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

//    private static Random rand = new Random(AMLSim.getSeed());
    private static Random rand = AMLSim.getRandom();
    private static Properties prop = null;

    private static float SAR2SAR_EDGE_THRESHOLD = 0.0F;
    private static float SAR2NORMAL_EDGE_THRESHOLD = 0.0F;
    private static float NORMAL2SAR_EDGE_THRESHOLD = 0.0F;
    private static float NORMAL2NORMAL_EDGE_THRESHOLD = 0.0F;
    
    private static float SAR2SAR_TX_PROB = 1.0F;
    private static float SAR2NORMAL_TX_PROB = 1.0F;
    private static float NORMAL2SAR_TX_PROB = 1.0F;
    private static float NORMAL2NORMAL_TX_PROB = 1.0F;

    private static float SAR2SAR_AMOUNT_RATIO = 1.0F;
    private static float SAR2NORMAL_AMOUNT_RATIO = 1.0F;
    private static float NORMAL2SAR_AMOUNT_RATIO = 1.0F;
    private static float NORMAL2NORMAL_AMOUNT_RATIO = 1.0F;

    private static float NORMAL_HIGH_RATIO = 1.0F;  // High transaction amount ratio from normal accounts
    private static float NORMAL_LOW_RATIO = 1.0F;  // Low transaction amount ratio from normal accounts
    private static float NORMAL_HIGH_PROB = 0.0F;  // Probability of transactions with high amount
    private static float NORMAL_LOW_PROB = 0.0F;  // Probability of transactions with low amount
    private static float NORMAL_SKIP_PROB = 0.0F;  // Probability of skipping transactions

    /**
     * Whether it adjusts parameters of normal transactions
     * @return If true, it affects to normal transaction models
     * If false, it does not any effects to all normal transactions
     */
    public static boolean isValid(){
        return prop != null;
    }
    
    private static float getRatio(String key, float defaultValue){
        String value = System.getProperty(key);
        if(value == null){
            value = prop.getProperty(key, String.valueOf(defaultValue));
        }
        return Float.parseFloat(value);
    }

    private static float getRatio(String key){
        return getRatio(key, 1.0F);
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
        
        SAR2SAR_TX_PROB = getRatio("sar2sar.tx.prob");
        SAR2NORMAL_TX_PROB = getRatio("sar2normal.tx.prob");
        NORMAL2SAR_TX_PROB = getRatio("normal2sar.tx.prob");
        NORMAL2NORMAL_TX_PROB = getRatio("normal2normal.tx.prob");

        SAR2SAR_AMOUNT_RATIO = getRatio("sar2sar.amount.ratio");
        SAR2NORMAL_AMOUNT_RATIO = getRatio("sar2normal.amount.ratio");
        NORMAL2SAR_AMOUNT_RATIO = getRatio("normal2sar.amount.ratio");
        NORMAL2NORMAL_AMOUNT_RATIO = getRatio("normal2normal.amount.ratio");

        NORMAL_HIGH_RATIO = getRatio("normal.high.ratio", 1.0F);
        NORMAL_LOW_RATIO = getRatio("normal.low.ratio", 1.0F);
        NORMAL_HIGH_PROB = getRatio("normal.high.prob", 1.0F);
        NORMAL_LOW_PROB = getRatio("normal.low.prob", 1.0F);
        NORMAL_SKIP_PROB = getRatio("normal.skip.prob", 1.0F);
        if(NORMAL_HIGH_RATIO < 1.0){
            throw new IllegalArgumentException("The high transaction amount ratio must be 1.0 or more");
        }
        if(NORMAL_LOW_RATIO <= 0.0 || 1.0 < NORMAL_LOW_RATIO){
            throw new IllegalArgumentException("The low transaction amount ratio must be positive and 1.0 or less");
        }
        if(1.0 < NORMAL_HIGH_PROB + NORMAL_LOW_PROB + NORMAL_SKIP_PROB){
            throw new IllegalArgumentException("The sum of high, low and skip transaction probabilities" +
                                                       " must be 1.0 or less");
        }

        System.out.println("Transaction Probability:");
        System.out.println("\tSAR -> SAR: " + SAR2SAR_TX_PROB);
        System.out.println("\tSAR -> Normal: " + SAR2NORMAL_TX_PROB);
        System.out.println("\tNormal -> SAR: " + NORMAL2SAR_TX_PROB);
        System.out.println("\tNormal -> Normal: " + NORMAL2NORMAL_TX_PROB);

        System.out.println("Transaction edge addition threshold (proportion of SAR accounts):");
        System.out.println("\tSAR -> SAR: " + SAR2SAR_EDGE_THRESHOLD);
        System.out.println("\tSAR -> Normal: " + SAR2NORMAL_EDGE_THRESHOLD);
        System.out.println("\tNormal -> SAR: " + NORMAL2SAR_EDGE_THRESHOLD);
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

        if(!isValid()){
            return amount;
        }

        float ratio;
        float prob = rand.nextFloat();
        
        if(orig.isSAR()){  // SAR originator
            if(bene.isSAR()){  // SAR -> SAR
                if(SAR2SAR_TX_PROB <= prob){
                    return 0.0F;
                }
                ratio = SAR2SAR_AMOUNT_RATIO;
            }else{  // SAR -> Normal
                if(SAR2NORMAL_TX_PROB <= prob){
                    return 0.0F;
                }
                ratio = SAR2NORMAL_AMOUNT_RATIO;
            }
        }else{  // Normal originator
            if(bene.isSAR()){  // Normal -> SAR
                if(NORMAL2SAR_TX_PROB <= prob){
                    return 0.0F;
                }
                ratio = NORMAL2SAR_AMOUNT_RATIO;
            }else{  // Normal -> Normal
                if(NORMAL2NORMAL_TX_PROB <= prob){
                    return 0.0F;
                }
                ratio = NORMAL2NORMAL_AMOUNT_RATIO;
            }
            
            prob = rand.nextFloat();
            if(prob < NORMAL_HIGH_PROB){  // High-amount payment transaction (near to the upper limit)
                ratio *= NORMAL_HIGH_RATIO;
            }else if(prob < NORMAL_HIGH_PROB + NORMAL_LOW_PROB){  // Low-amount transaction
                ratio *= NORMAL_LOW_RATIO;
            }else if(prob < NORMAL_HIGH_PROB + NORMAL_LOW_PROB + NORMAL_SKIP_PROB){
                return 0.0F;  // Skip this transaction
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
        if(!isValid()){  // It always adds this edge
            return true;
        }
        // Proportion of SAR beneficiary accounts of the originator account
//        float benePropThreshold = SAR2NORMAL_EDGE_THRESHOLD;
//        int beneNumThreshold = (int) Math.floor(1 / NORMAL2SAR_EDGE_THRESHOLD);

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
                return numNeighbors > (int) Math.floor(1 / NORMAL2SAR_EDGE_THRESHOLD)
                        && propSARBene >= NORMAL2SAR_EDGE_THRESHOLD;
            }else{  // Normal -> Normal
                return propSARBene >= NORMAL2NORMAL_EDGE_THRESHOLD;
            }
        }
    }

}
