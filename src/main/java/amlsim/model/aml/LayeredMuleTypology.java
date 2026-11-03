// Added by EarlyMule-TG (2026-11-03): layered mule typology used for the mule patterns M1-M4.
// See EARLYMULE-TG.md, section 4.
package amlsim.model.aml;

import amlsim.AMLSim;
import amlsim.Account;

import java.util.*;

/**
 * Money enters at layer 0 (sources), passes through one or more mule layers and leaves at the last
 * layer (exits). Consecutive layers are linked all-to-all when either has one account, otherwise
 * one-to-one by position. A mule forwards only after all its planned inflows have fired, and it
 * forwards the illicit amount received minus the margin, capped by its balance. Transfers never
 * exceed the sender's balance, so balance columns in the log cannot reveal illicit transfers.
 */
public class LayeredMuleTypology extends AMLTypology {

    /** One planned illicit transfer between consecutive layers. */
    private static class Edge {
        Account orig, bene;
        int fromLayer;
        long step = -1;  // -1 until the sender is ready
        double amount;
        boolean done;
    }

    private final Map<Account, Integer> layerOf = new HashMap<>();
    private final List<List<Account>> layers = new ArrayList<>();
    private final List<Edge> edges = new ArrayList<>();
    private final Map<Account, List<Edge>> inEdges = new HashMap<>();
    private final Map<Account, List<Edge>> outEdges = new HashMap<>();
    private final Map<Account, Double> received = new HashMap<>();
    private int minDwell = 0;
    private int maxDwell = 0;
    private long sourceEnd;  // Last step for source transfers
    private final Random random = AMLSim.getRandom();

    LayeredMuleTypology(double minAmount, double maxAmount, int startStep, int endStep) {
        super(minAmount, maxAmount, startStep, endStep);
    }

    /** Record the layer of a member (called by the alert loader, before setParameters). */
    public void setMemberLayer(Account acct, int layer) {
        if (layer < 0) {
            throw new IllegalArgumentException("Layered mule member without a layer: " + acct.getID());
        }
        layerOf.put(acct, layer);
    }

    /** Days a mule holds money before forwarding, drawn per outgoing transfer from [min, max]. */
    public void setDwell(int min, int max) {
        if (min < 0 || max < min) {
            throw new IllegalArgumentException("Invalid dwell range: " + min + "-" + max);
        }
        minDwell = min;
        maxDwell = max;
    }

    /**
     * Build layers and edges, then schedule the source transfers.
     * @param scheduleID unused; timing follows the dwell range
     */
    @Override
    public void setParameters(int scheduleID) {
        // 1. Group members by layer, keeping file order inside a layer
        int numLayers = Collections.max(layerOf.values()) + 1;
        for (int l = 0; l < numLayers; l++) {
            layers.add(new ArrayList<>());
        }
        for (Account acct : alert.getMembers()) {
            layers.get(layerOf.get(acct)).add(acct);
        }
        for (List<Account> layer : layers) {
            if (layer.isEmpty() || numLayers < 3) {
                throw new IllegalArgumentException("Alert " + alert.getAlertID() + " needs >= 3 non-empty layers");
            }
        }

        // 2. Edges between consecutive layers
        for (int l = 0; l < numLayers - 1; l++) {
            List<Account> from = layers.get(l), to = layers.get(l + 1);
            if (from.size() == 1 || to.size() == 1) {
                for (Account o : from) for (Account b : to) addEdge(o, b, l);
            } else if (from.size() == to.size()) {
                for (int i = 0; i < from.size(); i++) addEdge(from.get(i), to.get(i), l);
            } else {
                throw new IllegalArgumentException("Alert " + alert.getAlertID() + ": layers " + l + " and "
                        + (l + 1) + " have sizes " + from.size() + " and " + to.size());
            }
        }

        // 3. Source transfers fall inside the source window; the generator reserved maxDwell
        //    days per mule layer after it, so later hops stay inside [startStep, endStep]
        sourceEnd = endStep - (long) (numLayers - 2) * maxDwell;
        if (sourceEnd < startStep) {
            throw new IllegalArgumentException("Alert " + alert.getAlertID() + ": window too short for dwell");
        }
        for (Edge e : edges) {
            if (e.fromLayer == 0) {
                e.step = startStep + (long) (random.nextDouble() * (sourceEnd - startStep + 1));
                e.amount = minAmount + random.nextDouble() * (maxAmount - minAmount);
            }
        }
    }

    private void addEdge(Account orig, Account bene, int fromLayer) {
        Edge e = new Edge();
        e.orig = orig;
        e.bene = bene;
        e.fromLayer = fromLayer;
        edges.add(e);
        outEdges.computeIfAbsent(orig, k -> new ArrayList<>()).add(e);
        inEdges.computeIfAbsent(bene, k -> new ArrayList<>()).add(e);
    }

    @Override
    public String getModelName() {
        return "LayeredMuleTypology";
    }

    /** Fire the transfers due at this step, lower layers first so a zero-day dwell forwards in the same step. */
    @Override
    public void sendTransactions(long step, Account acct) {
        for (int l = 0; l < layers.size() - 1; l++) {
            for (Edge e : edges) {
                if (e.fromLayer == l && !e.done && e.step == step) {
                    fire(e, step);
                }
            }
        }
    }

    private void fire(Edge e, long step) {
        // 1. A source short of money waits a day, until the source window closes
        if (e.fromLayer == 0 && e.orig.getBalance() < minAmount && step < sourceEnd) {
            e.step = step + 1;
            return;
        }
        // 2. Send at most the current balance; a skipped transfer still counts as resolved
        double amount = Math.min(e.amount, e.orig.getBalance());
        if (amount > 0) {
            makeTransaction(step, amount, e.orig, e.bene, alert.isSAR(), alert.getAlertID());
            received.merge(e.bene, amount, Double::sum);
        }
        e.done = true;

        // 3. A mule becomes ready once every planned inflow is resolved
        Account next = e.bene;
        boolean isMule = layerOf.get(next) < layers.size() - 1;
        if (isMule && inEdges.get(next).stream().allMatch(x -> x.done)) {
            scheduleForward(next, step);
        }
    }

    private void scheduleForward(Account mule, long readyStep) {
        // Forward only the illicit amount received (minus margin), split with random weights
        List<Edge> outs = outEdges.get(mule);
        double available = received.getOrDefault(mule, 0.0) * (1 - marginRatio);
        double[] w = new double[outs.size()];
        double total = 0;
        for (int i = 0; i < w.length; i++) {
            w[i] = 0.5 + random.nextDouble();
            total += w[i];
        }
        for (int i = 0; i < outs.size(); i++) {
            Edge e = outs.get(i);
            e.amount = available * w[i] / total;
            int dwell = minDwell + random.nextInt(maxDwell - minDwell + 1);
            e.step = Math.min(readyStep + dwell, endStep);
        }
    }
}
